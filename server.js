require("dotenv").config();

const express = require("express");
const mongoose = require("mongoose");
const fs = require("fs");
const path = require("path");

const app = express();
const port = Number(process.env.PORT || 8002);
const staticRoot = path.resolve(__dirname, "cloned_site");
const mongoUri = process.env.MONGODB_URI;
const captureScriptTag = '<script src="/submission-capture.js"></script>';

const submissionSchema = new mongoose.Schema(
  {
    formId: { type: String, required: true, trim: true, maxlength: 200 },
    pageUrl: { type: String, trim: true, maxlength: 2000 },
    data: { type: mongoose.Schema.Types.Mixed, required: true },
    submittedAt: { type: Date, required: true, default: Date.now },
    clientSubmissionId: {
      type: String,
      trim: true,
      maxlength: 100,
      unique: true,
      sparse: true,
    },
  },
  { collection: "submissions" },
);

const Submission = mongoose.model("Submission", submissionSchema);

app.use(express.json({ limit: "1mb" }));

app.get("/api/health", (_req, res) => {
  res.json({ ok: true, mongo: mongoose.connection.readyState === 1 });
});

app.get("/submission-capture.js", (_req, res) => {
  res.sendFile(path.join(__dirname, "submission-capture.js"));
});

app.post("/api/submit", async (req, res) => {
  const { formId, pageUrl, data, clientSubmissionId } = req.body || {};

  if (typeof formId !== "string" || !formId.trim()) {
    return res.status(400).json({ error: "formId is required" });
  }

  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return res.status(400).json({ error: "data must be an object" });
  }

  try {
    const submissionFields = {
      formId: formId.trim(),
      pageUrl: typeof pageUrl === "string" ? pageUrl : undefined,
      data,
      submittedAt: new Date(),
    };

    let submission;
    if (typeof clientSubmissionId === "string" && clientSubmissionId.trim()) {
      submission = await Submission.findOneAndUpdate(
        { clientSubmissionId: clientSubmissionId.trim() },
        {
          $set: submissionFields,
          $setOnInsert: { clientSubmissionId: clientSubmissionId.trim() },
        },
        { new: true, upsert: true, runValidators: true, setDefaultsOnInsert: true },
      );
    } else {
      submission = await Submission.create(submissionFields);
    }

    return res.status(201).json({ ok: true, id: submission._id });
  } catch (error) {
    console.error("Failed to save form submission:", error);
    return res.status(500).json({ error: "Unable to save submission" });
  }
});

// Serve the cloned HTML while injecting the capture script. This avoids
// editing the generated one-line Next.js HTML artifact.
app.use((req, res, next) => {
  if (req.method !== "GET") return next();

  const requestPath = decodeURIComponent(req.path);
  const candidate = path.resolve(staticRoot, `.${requestPath}`);
  const htmlPath = path.extname(requestPath)
    ? candidate
    : `${candidate}.html`;
  const rootPrefix = `${staticRoot}${path.sep}`;

  if (!htmlPath.startsWith(rootPrefix) || !fs.existsSync(htmlPath)) {
    return next();
  }

  if (path.extname(htmlPath).toLowerCase() !== ".html") return next();

  const html = fs.readFileSync(htmlPath, "utf8");
  const withCaptureScript = html.replace("</head>", `${captureScriptTag}</head>`);
  res.type("html").send(withCaptureScript);
});

app.use(express.static(staticRoot, {
  setHeaders: (res, filePath) => {
    // Local clones can retain stale generated JavaScript after an asset is
    // repaired. Avoid serving an old cached copy during local testing.
    if (filePath.toLowerCase().endsWith(".js")) {
      res.setHeader("Cache-Control", "no-store");
    }
  },
}));

async function start() {
  if (!mongoUri) {
    throw new Error("MONGODB_URI is not set. Copy .env.example to .env and configure it.");
  }

  await mongoose.connect(mongoUri);
  app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
    console.log('MongoDB connected; submissions use the "submissions" collection.');
  });
}

start().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
