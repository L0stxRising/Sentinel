// old sensor polling attempt from local node server
// function startLivePolling() {
//     setInterval(() => {
//         fetch("http://localhost:8080/drain/node-01")
//             .then(r => r.json())
//             .then(d => {
//                 if (d && d.water_level) console.log("live wl:", d.water_level);
//             })
//             .catch(err => console.log("offline mode"));
//     }, 3000);
// }
// startLivePolling();

var probTxt = "Every monsoon, city drains get clogged with plastic, silt, and garbage, causing severe waterlogging, traffic gridlock, and the spread of dangerous diseases like dengue and cholera. Right now, authorities only clean drains after water overflows onto the streets. Sanitation workers are then forced to risk their lives diving into toxic, flooded drains during emergency cleanups. This project will help cities catch blockages days before an overflow happens, making drain maintenance planned, safe, and cost-effective.";
document.getElementById("problemText").textContent = probTxt;

var aboutTxt = "Project Sentinel is a low-cost, smart underground drain monitoring network designed to predict water blockages and alert municipal authorities before street flooding occurs. It uses radar-based water level sensors deployed inside manholes, connected through a LoRa mesh network for long-range communication. Each node runs on a lithium battery pack with deep-sleep cycles, lasting up to 2 years without maintenance. The collected data is fed into an LSTM-based AI model that learns the normal drainage patterns of each location and flags anomalies — like unusually slow drainage or rising water levels — days before an actual overflow. This shifts drain maintenance from reactive emergency cleanups to safe, planned interventions.";
document.getElementById("aboutText").textContent = aboutTxt;

// old tab switcher attempt - removed cuz single page scroll is better
// var tabs = document.querySelectorAll(".tab-btn");
// tabs.forEach(function(t) {
//     t.addEventListener("click", function() {
//         var target = this.dataset.tab;
//         document.querySelectorAll(".tab-content").forEach(function(c) {
//             c.style.display = "none";
//         });
//         document.querySelectorAll(".tab-btn").forEach(function(b) {
//             b.classList.remove("active");
//         });
//         document.getElementById(target).style.display = "block";
//         this.classList.add("active");
//     });
// });

var mats = [
    { name: "Radar Water Sensor", desc: "Measures water level inside the manhole without touching dirty sewage." },
    { name: "Microcontroller Board", desc: "Handles sensor readings and manages power-saving deep sleep modes." },
    { name: "LoRa Transceiver Modules", desc: "Long-range radio communication between underground nodes." },
    { name: "Lithium Battery Pack", desc: "Powers each underground node for up to 2 years using deep-sleep cycles." }
];
document.getElementById("matGrid").innerHTML = mats.map(m => `<div class="mat-card"><h3>${m.name}</h3><p>${m.desc}</p></div>`).join("");

// old canvas wave simulator - killed it, video is cleaner
// function initMiniCanvas() {
//     var c = document.getElementById("waterSimCanvas");
//     if (!c) return;
//     var ctx = c.getContext("2d");
//     ctx.fillStyle = "#0077be";
//     ctx.fillRect(0, 50, 200, 100);
// }

var steps = [
    { title: "Sense", desc: "The ultrasonic sensor measures the water level without touching the sewage, then enters deep sleep to save battery." },
    { title: "Communicate", desc: "LoRa sends the reading through the node network, automatically rerouting around failed nodes." },
    { title: "Store", desc: "A gateway forwards the data to a central database, building a historical record of each drain." },
    { title: "Think", desc: "The LSTM model compares current drainage patterns with historical behavior to detect unusually slow drainage that may indicate a developing blockage." },
    { title: "Act", desc: "The system generates a risk score and alerts authorities through the dashboard, allowing them to act before an overflow occurs." }
];
document.getElementById("stepsList").innerHTML = steps.map((s, i) => `<div class="step-item"><div class="step-num">${i + 1}</div><div><h3>${s.title}</h3><p>${s.desc}</p></div></div>`).join("");

var aiDesc = "The AI model uses an LSTM (Long Short-Term Memory) network to learn the normal water-level behavior of each drain by analyzing historical data collected over hours, days, and weeks. Instead of relying on a fixed threshold, it studies the relationship between past and current readings to understand long-term patterns. This allows it to avoid falsely flagging a random upsurge or downsurge caused by temporary rainfall, sudden water flow, or other short-term fluctuations. The model focuses on persistent and unusual changes, such as water levels gradually rising or remaining elevated for longer than expected, which may indicate a developing blockage. When such an anomaly is detected, the system generates a risk score to indicate the likelihood of a potential blockage.";
document.getElementById("aiText").textContent = aiDesc;

var utils = [
    { title: "Prevents Urban Waterlogging", desc: "By predicting blockages days before heavy rainfall, authorities can clear drains early, preventing severe street flooding and citywide traffic gridlocks." },
    { title: "Protects Public Health", desc: "Prevents stagnant sewage water from overflowing onto public roads, directly eliminating mosquito breeding grounds and preventing outbreaks of waterborne diseases like dengue and cholera." },
    { title: "Safeguards Sanitation Workers", desc: "Replaces dangerous emergency drain-diving in toxic, flooded conditions with safe, planned maintenance interventions." },
    { title: "Saves Municipal Funds", desc: "Shifts city maintenance from wasteful, fixed-schedule cleaning to targeted, condition-based cleaning, saving taxpayer money and optimizing labor." },
    { title: "Real-Time City Insights", desc: "Supplies municipal planners with historical flow data to identify chronically undersized or damaged drainage pipes across the urban network." }
];
document.getElementById("utilGrid").innerHTML = utils.map(u => `<div class="util-item"><h3>${u.title}</h3><p>${u.desc}</p></div>`).join("");

var novelties = [
    "Predictive AI over Basic Alarm",
    "Underground Relay Network",
    "Custom Drain Baselines",
    "Low-Cost & Long Battery Life"
];
document.getElementById("noveltyRow").innerHTML = novelties.map(n => `<div class="n-tag">${n}</div>`).join("");

// function toggleRiskModal() {
//     var m = document.getElementById("riskModal");
//     if (m) m.classList.toggle("visible");
// }
