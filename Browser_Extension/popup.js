document.addEventListener('DOMContentLoaded', function() {
    chrome.storage.local.get(['currentUrl', 'currentPrediction'], function(data) {
      if (data.currentUrl && data.currentPrediction) {
        const url = new URL(data.currentUrl);
        document.getElementById('currentUrl').textContent = url.hostname;
        
        const statusElement = document.getElementById('status');
        if (data.currentPrediction === "BEWARE MALICIOUS WEBSITE") {
          statusElement.textContent = "Potentially Malicious";
          statusElement.className = "malicious";
        } else {
          statusElement.textContent = "Safe";
          statusElement.className = "safe";
        }
      } else {
        document.getElementById('currentUrl').textContent = "No website scanned yet";
        document.getElementById('status').textContent = "";
      }
    });
  });