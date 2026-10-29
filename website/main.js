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
document.getElementById("stepsList").innerHTML = steps.map((s, i) => `<div class="step-item"><span class="step-num">${i + 1}.</span><div><h3>${s.title}</h3><p>${s.desc}</p></div></div>`).join("");

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

// function toggleRiskModal() {
//     var m = document.getElementById("riskModal");
//     if (m) m.classList.toggle("visible");
// }


// onnx ai inference logic
// scaler params from scaler.pkl
var s_min = [-0.5336516754213162, -0.4411764705882353, 0.0, 0.0, -0.09953410214997768, -0.0020799321609858315, -0.0022994246400764684, -0.0010103866608125777, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0];
var s_scale = [0.04060069556722197, 0.014705882352941176, 0.045414975119779835, 0.003784581259981653, 0.3636492386590745, 0.0015095808335452963, 0.001511626472144357, 0.011778979647408972, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0];

var sim_buf = [];
// keep track of ticks from iframe
window.addEventListener("message", function(e) {
    try {
        var d = typeof e.data === 'string' ? JSON.parse(e.data) : e.data;
        if (d && d.level_cm !== undefined) {
            sim_buf.push(d);
            if (sim_buf.length > 24) sim_buf.shift();
        }
    } catch(err) {}
});

var m_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

function extractFeats(st) {
    var hr = st.hour !== undefined ? st.hour : 12;
    var mon = st.month || "January";
    var m_num = m_names.indexOf(mon) + 1;
    if (m_num < 1) m_num = 1;
    var szn = st.season || "winter";
    var wx = st.weather_state || "clear";

    var h_sin = Math.sin(2 * Math.PI * hr / 23.0);
    var h_cos = Math.cos(2 * Math.PI * hr / 23.0);
    var m_sin = Math.sin(2 * Math.PI * m_num / 12.0);
    var m_cos = Math.cos(2 * Math.PI * m_num / 12.0);

    var v = [
        st.temp_c || 20.0,
        st.rh_pct || 55.0,
        st.rain_mm || 0.0,
        st.rain_mm || 0.0,
        st.demand_index || 1.0,
        st.inflow_lps || 5.0,
        st.smoothed_flow_lps || 5.0,
        st.level_cm || 0.0,
        h_sin,
        h_cos,
        m_sin,
        m_cos,
        szn == "winter" ? 1.0 : 0.0,
        szn == "pre_monsoon" ? 1.0 : 0.0,
        szn == "monsoon" ? 1.0 : 0.0,
        szn == "post_monsoon" ? 1.0 : 0.0,
        wx == "clear" ? 1.0 : 0.0,
        wx == "cloudy" ? 1.0 : 0.0,
        wx == "drizzle" ? 1.0 : 0.0,
        wx == "light_rain" ? 1.0 : 0.0,
        wx == "moderate_rain" ? 1.0 : 0.0,
        wx == "heavy_rain" ? 1.0 : 0.0
    ];

    for (var k = 0; k < 22; k++) {
        v[k] = v[k] * s_scale[k] + s_min[k];
    }
    return v;
}

var ort_session = null;
var threshold = 0.00321;
// var threshold = 0.015;

async function runAnalyze() {
    var outBox = document.getElementById("modelRes");
    if (!outBox) return;
    outBox.textContent = "Running ONNX inference...";
    outBox.style.color = "#8b949e";

    try {
        if (!ort_session) {
            // ort_session = await ort.InferenceSession.create('onnxModel.onnx', { executionProviders: ['wasm'] });
            ort_session = await ort.InferenceSession.create('./onnxModel.onnx');
        }

        var win = [];
        if (sim_buf.length === 0) {
            var def_st = {hour: 12, month: "January", season: "winter", weather_state: "clear", temp_c: 20.0, rh_pct: 55.0, rain_mm: 0.0, demand_index: 0.8, inflow_lps: 4.8, smoothed_flow_lps: 4.8, level_cm: 1.2};
            for (var i = 0; i < 24; i++) win.push(extractFeats(def_st));
        } else {
            var tmp = sim_buf.slice();
            while (tmp.length < 24) {
                tmp.unshift(tmp[0]);
            }
            for (var i = 0; i < 24; i++) {
                win.push(extractFeats(tmp[i]));
            }
        }

        // repeat sequence across 64 batches as model requires [64, 24, 22]
        var inpData = new Float32Array(64 * 24 * 22);
        for (var b = 0; b < 64; b++) {
            for (var t = 0; t < 24; t++) {
                for (var f = 0; f < 22; f++) {
                    inpData[b * 24 * 22 + t * 22 + f] = win[t][f];
                }
            }
        }

        var inpTensor = new ort.Tensor('float32', inpData, [64, 24, 22]);
        var inName = ort_session.inputNames[0];
        var feeds = {};
        feeds[inName] = inpTensor;

        var results = await ort_session.run(feeds);
        var outName = ort_session.outputNames[0];
        var outData = results[outName].data;

        // compute reconstruction MAE on batch 0
        var diff = 0.0;
        for (var idx = 0; idx < 24 * 22; idx++) {
            diff += Math.abs(outData[idx] - inpData[idx]);
        }
        var loss = diff / (24 * 22);
        var is_anamoly = loss > threshold;

        // console.log("inference done loss:", loss);
        outBox.textContent = "Loss: " + loss.toFixed(6) + " | Threshold: " + threshold + " | Output: " + (is_anamoly ? "ANOMALY (Blockage Detected)" : "NORMAL");
        outBox.style.color = is_anamoly ? "#f85149" : "#3fb950";

    } catch (e) {
        console.log("inference err:", e);
        outBox.textContent = "Inference Error: " + (e.message || e);
        outBox.style.color = "#f85149";
    }
}
