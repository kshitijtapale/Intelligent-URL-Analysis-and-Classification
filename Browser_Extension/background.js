const API_URL = 'http://localhost:8000/api/predict_url';

// Keep track of tab statuses
const tabStatuses = {};

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && !tab.url.startsWith("chrome://") && !tab.url.startsWith("chrome-extension://")) {
    checkURL(tab.url, tabId);
  }
});

chrome.tabs.onActivated.addListener((activeInfo) => {
  updateIconForTab(activeInfo.tabId);
});

function updateIconForTab(tabId) {
  const status = tabStatuses[tabId];
  if (status === 'malicious') {
    chrome.browserAction.setIcon({
      path: {
        "16": "icons/danger16.png",
        "48": "icons/danger48.png",
        "128": "icons/danger128.png"
      },
      tabId: tabId
    });
  } else {
    chrome.browserAction.setIcon({
      path: {
        "16": "icons/safe16.png",
        "48": "icons/safe48.png",
        "128": "icons/safe128.png"
      },
      tabId: tabId
    });
  }
}

function checkURL(url, tabId) {
  console.log("Checking URL:", url);
  fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url: url }),
  })
  .then(response => response.json())
  .then(data => {
    console.log("API response:", data);
    if (data.result === "BEWARE MALICIOUS WEBSITE") {
      console.log("Malicious website detected. Redirecting to blocked page.");
      tabStatuses[tabId] = 'malicious';
      updateIconForTab(tabId);
      const encodedUrl = encodeURIComponent(url);
      const blockedPageUrl = chrome.runtime.getURL(`blocked.html?blockedUrl=${encodedUrl}`);
      chrome.tabs.update(tabId, {url: blockedPageUrl});
      
      showMaliciousNotification(url);
    } else {
      console.log("Safe website detected.");
      tabStatuses[tabId] = 'safe';
      updateIconForTab(tabId);
      showSafeNotification(url);
    }
    updatePopup(url, data.result);
  })
  .catch(error => console.error('Error:', error));
}

function showSafeNotification(url) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/safe48.png',
    title: 'Safe Website',
    message: `${new URL(url).hostname} is safe to browse.`,
    priority: 0
  });
}

function showMaliciousNotification(url) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/danger48.png',
    title: 'Malicious Website Detected',
    message: `${new URL(url).hostname} may be dangerous.`,
    priority: 2
  });
}

function updatePopup(url, result) {
  chrome.storage.local.set({
    currentUrl: url,
    currentPrediction: result
  });
}