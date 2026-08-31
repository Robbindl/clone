(function installSubmissionCapture() {
  "use strict";

  var sessionData = {};
  var sessionId = window.crypto && window.crypto.randomUUID
    ? window.crypto.randomUUID()
    : String(Date.now()) + Math.random().toString(16).slice(2);
  var pendingTimer;

  function addValue(target, name, value) {
    if (Object.prototype.hasOwnProperty.call(target, name)) {
      target[name] = Array.isArray(target[name])
        ? target[name].concat(value)
        : [target[name], value];
    } else {
      target[name] = value;
    }
  }

  function readForm(form) {
    var data = {};
    var controls = form.querySelectorAll("input, textarea, select");

    controls.forEach(function (control) {
      var name = control.name;
      if (!name || control.disabled) return;

      if ((control.type === "checkbox" || control.type === "radio") && !control.checked) {
        return;
      }

      if (control.type === "file") {
        addValue(data, name, Array.from(control.files || []).map(function (file) {
          return file.name;
        }));
        return;
      }

      if (control.tagName === "SELECT" && control.multiple) {
        addValue(data, name, Array.from(control.selectedOptions).map(function (option) {
          return option.value;
        }));
        return;
      }

      addValue(data, name, control.value);
    });

    return data;
  }

  function mergeFormData(form) {
    Object.assign(sessionData, readForm(form));
    return Object.assign({}, sessionData);
  }

  function persist(form) {
    var payload = {
      formId: window.location.pathname,
      pageUrl: window.location.href,
      data: mergeFormData(form),
      clientSubmissionId: sessionId,
    };

    fetch("/api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      keepalive: true,
    }).catch(function (error) {
      // Do not interrupt the cloned form's existing behavior.
      console.error("Local submission persistence failed:", error);
    });
  }

  function schedulePersist(form) {
    window.clearTimeout(pendingTimer);
    pendingTimer = window.setTimeout(function () {
      persist(form);
    }, 250);
  }

  function formFromEvent(event) {
    var target = event.target;
    if (!target || !target.closest) return null;
    return target.closest("form");
  }

  document.addEventListener("input", function (event) {
    var form = formFromEvent(event);
    if (form) schedulePersist(form);
  }, true);

  document.addEventListener("change", function (event) {
    var form = formFromEvent(event);
    if (form) schedulePersist(form);
  }, true);

  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!form || form.tagName !== "FORM") return;
    window.clearTimeout(pendingTimer);
    persist(form);
  }, true);
})();
