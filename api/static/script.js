// ===============================
// CONFIG
// ===============================
const API_BASE = "http://127.0.0.1:5000";

function getToken(){
  return localStorage.getItem("ys_token");
}

function authHeaders(){
  const token = getToken();

  return token
    ? { "Authorization": `Bearer ${token}` }
    : {};
}

function escapeHTML(value){
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function logApi(title, data){
  const log = document.getElementById("apiLog");

  if(!log) return;

  log.textContent = `${title}\n\n${JSON.stringify(data, null, 2)}`;
}

function showMessage(message){
  const box = document.getElementById("authMessage");

  if(box){
    box.textContent = message;
  }
}

function showFlash(message, type = "success") {
  const flash = document.createElement("div");
  flash.textContent = message;
  flash.style.cssText = `
    position: fixed;
    top: 80px;
    right: 20px;
    padding: 12px 20px;
    border-radius: 8px;
    background: ${type === "success" ? "#2dc4b3" : "#e74c3c"};
    color: #0f1a1f;
    font-weight: 600;
    font-size: 0.9rem;
    z-index: 9999;
    box-shadow: 0 8px 32px -8px rgba(0,0,0,.4);
    transition: opacity 0.5s ease;
  `;
  document.body.appendChild(flash);
  setTimeout(() => {
    flash.style.opacity = "0";
    setTimeout(() => flash.remove(), 500);
  }, 3000);
}

function showDashboard(){
  const dashboard = document.getElementById("dashboard");

  if(dashboard){
    dashboard.classList.remove("hidden");
    dashboard.scrollIntoView({ behavior:"smooth" });
  }
}

function hideDashboard(){
  const dashboard = document.getElementById("dashboard");

  if(dashboard){
    dashboard.classList.add("hidden");
  }
}

function getJobId(job){
  return job.id || job.job_id;
}

function getJobLink(job){
  return (
    job.apply_link ||
    job.job_apply_link ||
    job.job_google_link ||
    job.url ||
    job.link ||
    ""
  );
}


// ===============================
// MOBILE NAVIGATION
// ===============================
const navToggle = document.querySelector(".nav-toggle");
const navLinks = document.querySelector(".nav-links");

if(navToggle && navLinks){
  navToggle.addEventListener("click", () => {
    navLinks.classList.toggle("open");
  });
}

document.querySelectorAll(".nav-links a").forEach(link => {
  link.addEventListener("click", (e) => {
    const href = link.getAttribute("href");

    if(href.startsWith("#")){
      e.preventDefault();
      const target = document.querySelector(href);
      if(target) target.scrollIntoView({ behavior:"smooth" });
    }

    if(navLinks) navLinks.classList.remove("open");
  });
});


// ===============================
// SCROLL REVEAL ANIMATION
// ===============================
const revealElements = document.querySelectorAll(".reveal");

function revealOnScroll(){
  const triggerBottom = window.innerHeight * 0.85;

  revealElements.forEach(el => {
    const rect = el.getBoundingClientRect();

    if(rect.top < triggerBottom){
      el.classList.add("in");
    }
  });
}

window.addEventListener("scroll", revealOnScroll);
window.addEventListener("DOMContentLoaded", revealOnScroll);


// ===============================
// ACTIVE NAVIGATION LINK
// ===============================
function activateNavLink(){
  const currentPath = window.location.pathname;
  const navItems = document.querySelectorAll(".nav-links a");

  navItems.forEach(link => {
    link.classList.remove("active");

    const linkPath = link.getAttribute("href");

    if(currentPath === linkPath || (currentPath === "/" && linkPath === "/")){
      link.classList.add("active");
    }
  });
}

window.addEventListener("load", activateNavLink);


// ===============================
// PARALLAX BLOBS
// ===============================
const blobs = document.querySelectorAll(".blob");

window.addEventListener("mousemove", e => {
  const x = e.clientX / window.innerWidth;
  const y = e.clientY / window.innerHeight;

  blobs.forEach((blob, index) => {
    const speed = (index + 1) * 20;

    blob.style.transform = `
      translate(
        ${(x - 0.5) * speed}px,
        ${(y - 0.5) * speed}px
      )
    `;
  });
});


// ===============================
// BACK TO TOP BUTTON
// ===============================
const topBtn = document.createElement("button");

topBtn.innerHTML = "↑";
topBtn.classList.add("top-btn");

document.body.appendChild(topBtn);

Object.assign(topBtn.style, {
  position:"fixed",
  bottom:"20px",
  right:"20px",
  width:"50px",
  height:"50px",
  borderRadius:"50%",
  border:"none",
  background:"linear-gradient(135deg,#2dc4b3,#1ea899)",
  color:"#0f1a1f",
  fontSize:"1.2rem",
  fontWeight:"bold",
  cursor:"pointer",
  opacity:"0",
  pointerEvents:"none",
  transition:"all .3s ease",
  zIndex:"9999",
  boxShadow:"0 8px 32px -8px rgba(0,0,0,.4)"
});

window.addEventListener("scroll", () => {
  if(window.scrollY > 500){
    topBtn.style.opacity = "1";
    topBtn.style.pointerEvents = "auto";
  }else{
    topBtn.style.opacity = "0";
    topBtn.style.pointerEvents = "none";
  }
});

topBtn.addEventListener("click", () => {
  window.scrollTo({
    top:0,
    behavior:"smooth"
  });
});


// ===============================
// AUTH TABS
// ===============================
document.querySelectorAll(".auth-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".auth-tab").forEach(t => {
      t.classList.remove("active");
    });

    document.querySelectorAll(".auth-form").forEach(f => {
      f.classList.remove("active");
    });

    tab.classList.add("active");

    const formId = tab.dataset.tab === "login"
      ? "loginForm"
      : "registerForm";

    const form = document.getElementById(formId);

    if(form){
      form.classList.add("active");
    }
  });
});


// ===============================
// REGISTER
// ===============================
const registerForm = document.getElementById("registerForm");

if(registerForm){
  registerForm.addEventListener("submit", async event => {
    event.preventDefault();

    const payload = {
      full_name:
        document.getElementById("registerName")?.value?.trim() || "",

      email:
        document.getElementById("registerEmail")?.value?.trim() || "",

      password:
        document.getElementById("registerPassword")?.value || "",

      role:
        document.getElementById("registerRole")?.value || "student",

      career_interest:
        document.getElementById("careerInterest")?.value?.trim() || "",

      preferred_job_type:
        document.getElementById("preferredJobType")?.value || "",

      work_style:
        document.getElementById("workStyle")?.value || "",

      availability:
        document.getElementById("availability")?.value || "",
    };

    try{
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method:"POST",
        headers:{
          "Content-Type":"application/json"
        },
        body:JSON.stringify(payload)
      });

      const data = await res.json();

      logApi("REGISTER RESPONSE", data);

      if(!res.ok){
        showMessage(data.msg || data.error || "Registration failed");
        return;
      }

      showMessage("Account created successfully. Now login.");

      const loginTab = document.querySelector('[data-tab="login"]');

      if(loginTab){
        loginTab.click();
      }

    }catch(error){
      showMessage("Could not connect to backend.");

      logApi("REGISTER ERROR", {
        error:error.message
      });
    }
  });
}


// ===============================
// LOGIN
// ===============================
const loginForm = document.getElementById("loginForm");

if(loginForm){
  loginForm.addEventListener("submit", async event => {
    event.preventDefault();

    const payload = {
      email: document.getElementById("loginEmail")?.value || "",
      password: document.getElementById("loginPassword")?.value || ""
    };

    try{
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method:"POST",
        headers:{
          "Content-Type":"application/json"
        },
        body:JSON.stringify(payload)
      });

      const data = await res.json();

      logApi("LOGIN RESPONSE", data);

      if(!res.ok){
        showMessage(data.msg || data.error || "Login failed");
        return;
      }

      const token = data.access_token || data.token;

      if(token){
        localStorage.setItem("ys_token", token);
      }

      const userName =
        data.user?.full_name ||
        data.user?.name ||
        data.full_name ||
        data.name ||
        data.email ||
        payload.email;

      localStorage.setItem("ys_user_name", userName);

      const nameBox = document.getElementById("currentUserName");

      if(nameBox){
        nameBox.textContent = userName;
      }

      showMessage("Login successful.");

      setTimeout(() => {
        window.location.href = "/dashboard";
      }, 1000);

      await loadSavedResume();
      await loadMatches();
      await loadBookmarks();

    }catch(error){
      showMessage("Could not connect to backend.");
      logApi("LOGIN ERROR", { error:error.message });
    }
  });
}


// ===============================
// LOGOUT
// ===============================
const logoutBtn = document.getElementById("logoutBtn");

if(logoutBtn){
  logoutBtn.addEventListener("click", () => {
    localStorage.removeItem("ys_token");
    localStorage.removeItem("ys_user_name");

    window.location.href = "/";
  });
}


// ===============================
// RESUME UPLOAD
// ===============================
const uploadResumeBtn = document.getElementById("uploadResumeBtn");

if(uploadResumeBtn){
  uploadResumeBtn.addEventListener("click", async () => {
    const fileInput = document.getElementById("resumeFile");
    const status = document.getElementById("resumeStatus");

    if(!fileInput || !fileInput.files.length){
      showFlash("Choose a resume first.", "error");
      return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    if(status){
      status.textContent = "Uploading and processing resume...";
    }

    try{
      const res = await fetch(`${API_BASE}/api/resume/upload`, {
        method:"POST",
        headers:authHeaders(),
        body:formData
      });

      const data = await res.json();

      logApi("RESUME UPLOAD RESPONSE", data);

      if(!res.ok){
        if(status){
          status.textContent = data.msg || data.error || "Resume upload failed.";
        }

        return;
      }

      if(status){
        status.textContent = "Resume uploaded successfully.";
      }

      await loadSavedResume();
      await loadMatches();

    }catch(error){
      if(status){
        status.textContent = "Could not connect to backend.";
      }

      logApi("RESUME UPLOAD ERROR", { error:error.message });
    }
  });
}


function renderSkillTags(skills){
  const box = document.getElementById("skillTags");

  if(!box) return;

  if(typeof skills === "string"){
    skills = skills
      .split(",")
      .map(skill => skill.trim())
      .filter(Boolean);
  }

  if(!Array.isArray(skills)){
    skills = [];
  }

  if(!skills.length){
    box.innerHTML = `<span class="tag">No skills found yet</span>`;
    return;
  }

  box.innerHTML = skills
    .slice(0,20)
    .map(skill => `<span class="tag">${escapeHTML(skill)}</span>`)
    .join("");
}


async function loadSavedResume(){
  const status = document.getElementById("resumeStatus");

  if(!getToken()){
    return;
  }

  try{
    const res = await fetch(`${API_BASE}/api/resume/me`, {
      headers:authHeaders()
    });

    const data = await res.json();

    logApi("SAVED RESUME RESPONSE", data);

    if(!res.ok || !data.ok){
      if(status){
        status.textContent = "Could not check saved resume.";
      }
      return;
    }

    if(!data.has_resume){
      if(status){
        status.textContent = "No resume uploaded yet.";
      }

      renderSkillTags([]);
      return;
    }

    const filename = data.resume?.filename || "Saved resume";
    const uploadedAt = data.resume?.uploaded_at || "";

    if(status){
      status.innerHTML = `
        Resume already uploaded:
        <strong>${escapeHTML(filename)}</strong>
        ${uploadedAt ? `<br><small>Uploaded: ${escapeHTML(uploadedAt)}</small>` : ""}
      `;
    }

    renderSkillTags(data.skills || data.resume?.keywords || []);

  }catch(error){
    if(status){
      status.textContent = "Could not connect to backend.";
    }

    logApi("SAVED RESUME ERROR", { error:error.message });
  }
}


// ===============================
// PREFERENCES
// ===============================
const savePrefsBtn = document.getElementById("savePrefsBtn");

if(savePrefsBtn){
  savePrefsBtn.addEventListener("click", () => {
    const jobType =
      document.getElementById("jobTypePref")?.value ||
      document.getElementById("preferredJobType")?.value ||
      "";

    const location =
      document.getElementById("locationPref")?.value ||
      "";

    localStorage.setItem("ys_pref_job_type", jobType);
    localStorage.setItem("ys_pref_location", location);

    showFlash("Preferences saved successfully!");
    loadMatches();
  });
}


// ===============================
// JOB SEARCH
// ===============================
const searchJobsBtn = document.getElementById("searchJobsBtn");

if(searchJobsBtn){
  searchJobsBtn.addEventListener("click", async () => {
    const query =
      document.getElementById("jobSearchInput")?.value ||
      "software";

    const feed = document.getElementById("jobFeed");

    if(feed){
      feed.innerHTML = `<p class="muted">Searching jobs...</p>`;
    }

    try{
      const res = await fetch(`${API_BASE}/api/jobs/search?q=${encodeURIComponent(query)}&country=jm`, {
        headers:authHeaders()
      });

      const data = await res.json();

      logApi("JOB SEARCH RESPONSE", data);

      if(!res.ok){
        if(feed){
          feed.innerHTML = `<p class="muted">Could not search jobs.</p>`;
        }

        return;
      }

      const jobs = data.jobs || data.results || data;

      renderJobs(Array.isArray(jobs) ? jobs : []);

    }catch(error){
      logApi("JOB SEARCH ERROR", { error:error.message });

      if(feed){
        feed.innerHTML = `<p class="muted">Could not connect to backend.</p>`;
      }
    }
  });
}


// ===============================
// LOAD MATCHES
// ===============================
async function loadMatches(){
  const feed = document.getElementById("jobFeed");

  if(!feed) return;

  feed.innerHTML = `<p class="muted">Loading matched jobs...</p>`;

  try{
    const res = await fetch(`${API_BASE}/api/jobs/matches`, {
      headers:authHeaders()
    });

    const data = await res.json();

    logApi("MATCHES RESPONSE", data);

    if(!res.ok){
      feed.innerHTML = `<p class="muted">Could not load matches yet. Upload your resume first.</p>`;
      return;
    }

    const jobs = data.matches || data.jobs || data;

    renderJobs(Array.isArray(jobs) ? jobs : []);

  }catch(error){
    feed.innerHTML = `<p class="muted">Could not connect to backend.</p>`;
    logApi("MATCHES ERROR", { error:error.message });
  }
}


function calculatePreferenceScore(job){
  const careerInterest =
    document.getElementById("careerInterest")?.value ||
    document.getElementById("careerInterestPref")?.value ||
    "";

  const preferredJobType =
    document.getElementById("jobTypePref")?.value ||
    document.getElementById("preferredJobType")?.value ||
    localStorage.getItem("ys_pref_job_type") ||
    "";

  const workStyle =
    document.getElementById("workStylePref")?.value ||
    document.getElementById("workStyle")?.value ||
    "";

  let score = 0;

  const text = `
    ${job.title || ""}
    ${job.description || ""}
    ${job.company || ""}
    ${job.job_type || ""}
    ${job.city || ""}
    ${job.location || ""}
    ${job.country || ""}
  `.toLowerCase();

  if(careerInterest && text.includes(careerInterest.toLowerCase())){
    score += 0.40;
  }

  if(preferredJobType && text.includes(preferredJobType.toLowerCase())){
    score += 0.30;
  }

  if(workStyle && text.includes(workStyle.toLowerCase())){
    score += 0.30;
  }

  return Math.min(score, 1);
}


function getJobCategory(matchScore, prefScore){
  if(prefScore >= 50 && matchScore >= 25){
    return "Strong Preference + Good Match";
  }

  if(prefScore >= 50){
    return "Strong Preference + Needs Skills";
  }

  if(matchScore >= 25){
    return "Good Match + Low Preference";
  }

  return "Low Preference + Low Match";
}


function renderJobs(jobs){
  const feed = document.getElementById("jobFeed");

  if(!feed) return;

  if(!jobs.length){
    feed.innerHTML = `<p class="muted">No jobs found yet. Upload your resume or search jobs.</p>`;
    updateCareerReadiness(0);
    return;
  }

  let totalFinal = 0;

  const html = jobs.map(job => {
    const jobId = getJobId(job);

    const rawMatch =
      job.match_score ??
      job.similarity ??
      job.score ??
      0;

    const match = rawMatch <= 1
      ? Math.round(rawMatch * 100)
      : Math.round(rawMatch);

    const prefRaw =
      job.preference_score ??
      calculatePreferenceScore(job);

    const pref = prefRaw <= 1
      ? Math.round(prefRaw * 100)
      : Math.round(prefRaw);

    const finalScore = Math.round((match + pref) / 2);
    totalFinal += finalScore;

    const category = getJobCategory(match, pref);
    const jobLink = getJobLink(job);

    return `
      <div class="job-card">
        <h3>${escapeHTML(job.title || "Untitled Job")}</h3>

        <p class="muted">
          ${escapeHTML(job.company || "Unknown Company")}
          ·
          ${escapeHTML(job.city || job.location || job.country || "Jamaica")}
        </p>

        <div class="score-row">
          <span class="score-pill">Match ${match}%</span>
          <span class="score-pill">Preference ${pref}%</span>
          <span class="category-pill">${escapeHTML(category)}</span>
        </div>

        <p class="muted small">
          ${job.description ? escapeHTML(job.description.slice(0,180)) + "..." : "No description available."}
        </p>

        <div class="job-actions">
          ${
            jobLink
            ? `
              <a href="${escapeHTML(jobLink)}" target="_blank" class="btn primary-btn">
                Apply Now
              </a>
            `
            : ""
          }

          <button class="btn ghost-btn" onclick="viewJobDetails(${jobId})">
            View Details
          </button>

          <button class="btn ghost-btn" onclick="runGuidance(${jobId})">
            Guidance Mode
          </button>

          <button class="btn primary-btn" onclick="bookmarkJob(${jobId})">
            Bookmark
          </button>
        </div>
      </div>
    `;
  }).join("");

  feed.innerHTML = html;

  updateCareerReadiness(Math.round(totalFinal / jobs.length));
}


async function viewJobDetails(jobId){
  const panel = document.getElementById("guidancePanel");

  if(!panel) return;

  panel.innerHTML = `<p class="muted">Loading job details...</p>`;

  try{
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}`, {
      headers:authHeaders()
    });

    const data = await res.json();
    const job = data.job || data;

    logApi("JOB DETAILS RESPONSE", data);

    if(!res.ok){
      panel.innerHTML = `<p class="muted">Could not load job details.</p>`;
      return;
    }

    const realJobId = getJobId(job);
    const jobLink = getJobLink(job);

    panel.innerHTML = `
      <div style="border-bottom:1px solid rgba(255,255,255,0.08);padding-bottom:1rem;margin-bottom:1.5rem">
        <h3 style="margin:0 0 0.25rem">${escapeHTML(job.title || "Job Details")}</h3>
        <p class="muted" style="margin:0">${escapeHTML(job.company || "Unknown Company")} · ${escapeHTML(job.city || job.country || "Jamaica")}</p>

        ${job.salary_min ? `
          <p style="margin:0.5rem 0 0;font-size:0.85rem;color:#2dc4b3;font-weight:600">
            $${escapeHTML(String(job.salary_min))} – $${escapeHTML(String(job.salary_max))} / ${escapeHTML((job.salary_period || "").toLowerCase())}
          </p>
        ` : ""}
      </div>

      ${job.skills?.length ? `
        <div style="margin-bottom:1.5rem">
          <p class="muted small" style="margin:0 0 0.5rem">Required Skills</p>
          <div class="tag-list">
            ${job.skills.map(s => `<span class="tag">${escapeHTML(s)}</span>`).join("")}
          </div>
        </div>
      ` : ""}

      <div style="margin-bottom:1.5rem">
        <p class="muted small" style="margin:0 0 0.75rem">About this role</p>
        <div style="
          font-size:0.88rem;
          line-height:1.75;
          color:var(--text-muted,#8899a6);
          max-height:320px;
          overflow-y:auto;
          padding-right:0.5rem;
          white-space:pre-line;
        ">${escapeHTML(job.description || "No description available.")}</div>
      </div>

      <div class="job-actions">
        ${jobLink ? `
          <a href="${escapeHTML(jobLink)}" target="_blank" class="btn primary-btn">Apply Externally</a>
        ` : ""}
        <button class="btn ghost-btn" onclick="runGuidance(${realJobId})">Guidance Mode</button>
        <button class="btn primary-btn" onclick="bookmarkJob(${realJobId})">Bookmark</button>
      </div>
    `;

    panel.scrollIntoView({
      behavior:"smooth"
    });

  }catch(error){
    panel.innerHTML = `<p class="muted">Could not connect to backend.</p>`;
    logApi("JOB DETAILS ERROR", { error:error.message });
  }
}


function updateCareerReadiness(score){
  const box = document.getElementById("careerReadiness");

  if(box){
    box.textContent = `${score || "--"}%`;
  }
}


// ===============================
// GUIDANCE HELPERS
// ===============================
const SOFT_SKILLS_FRONTEND = new Set([
  // generic soft skills
  "communication", "teamwork", "attention to detail", "problem solving",
  "leadership", "time management", "critical thinking", "adaptability",
  "professionalism", "organization", "public speaking", "presentation",
  "research", "writing", "word", "microsoft office",
  "english", "documentation", "physics", "biology", "chemistry",
  "mathematics", "filing", "scheduling", "record keeping",

  // too generic to be a learnable step
  "software engineering", "full stack", "dashboard", "reporting",

  // non-technical skills irrelevant to software jobs
  "digital marketing", "social media", "content creation", "seo",
  "branding", "copywriting", "email marketing", "campaign management",
  "customer service", "sales", "retail", "cashier", "call center",
  "phone etiquette", "hospitality", "food service", "bartending",
  "housekeeping", "front desk", "tourism", "guest service",
  "accounting", "bookkeeping", "payroll", "invoicing",
  "teaching", "tutoring", "lesson planning", "classroom management",
  "patient care", "caregiving", "first aid", "healthcare support",
]);

function filterSoftSkills(steps) {
  return steps.filter(step => !SOFT_SKILLS_FRONTEND.has((step.learn || "").toLowerCase()));
}

function filterSoftSkillTags(skills) {
  return skills.filter(s => !SOFT_SKILLS_FRONTEND.has((s || "").toLowerCase()));
}

function costToTime(skillCost) {
  if (skillCost <= 1.8)  return "~1–2 weeks";
  if (skillCost <= 2.5)  return "~3–4 weeks";
  if (skillCost <= 3.5)  return "~1–2 months";
  if (skillCost <= 4.5)  return "~2–3 months";
  if (skillCost <= 5.5)  return "~3–6 months";
  if (skillCost <= 7.0)  return "~6–9 months";
  return "~9–12 months";
}

function isSoftwareJob(jobTitle) {
  const techTerms = ["developer", "engineer", "software", "backend", "frontend",
                     "data", "devops", "cloud", "web", "fullstack", "full stack", "programmer"];
  const title = (jobTitle || "").toLowerCase();
  return techTerms.some(term => title.includes(term));
}


// ===============================
// GUIDANCE MODE
// ===============================

async function runGuidance(jobId){
  const panel = document.getElementById("guidancePanel");

  if(!panel) return;

  panel.innerHTML = `<p class="muted">Generating roadmap...</p>`;

  try{
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/skill-path?target_score=0.85`, {
      headers:authHeaders()
    });

    const data = await res.json();

    logApi("GUIDANCE RESPONSE", data);

    if(!res.ok){
      panel.innerHTML = `<p class="muted">Could not generate guidance.</p>`;
      return;
    }

    const rawPath    = data.path || [];
    const rawMissing = data.missing_skills || [];

    const pathsExplored = data.explored_combinations || data.paths_explored || data.explored_paths || 0;

    const isTechJob     = isSoftwareJob(data.job?.title);
    const path          = isTechJob ? filterSoftSkills(rawPath)       : rawPath;
    const missingSkills = isTechJob ? filterSoftSkillTags(rawMissing) : rawMissing;

    const sortedPath = [...path].sort((a, b) => (b.improvement || 0) - (a.improvement || 0));

    panel.innerHTML = `
      <h3>${escapeHTML(data.job?.title || "Career Roadmap")}</h3>

      <div class="score-row">
        <span class="score-pill">Start ${Math.round(data.start_score || 0)}%</span>
         <span class="score-pill">Final ${Math.round((data.start_score || 0) + sortedPath.reduce((sum, s) => sum + (s.improvement || 0), 0))}%</span>
        <span class="score-pill">${data.reached_target ? "Target Reached" : "Keep Improving"}</span>
      </div>

      ${pathsExplored > 0 ? `
      <div style="
        margin: 1rem 0;
        padding: 0.75rem 1rem;
        background: rgba(13,122,95,0.08);
        border-left: 3px solid #2dc4b3;
        border-radius: 6px;
        font-size: 0.82rem;
        color: var(--text-muted, #8899a6);
      ">
        🔍 Dijkstra explored <strong style="color:#2dc4b3">${pathsExplored} skill combinations</strong>
        and selected the most efficient learning path
      </div>
      ` : ""}

      <h3 class="sub">Missing Skills</h3>
      <div class="tag-list">
        ${
          missingSkills.length
          ? missingSkills.map(skill => `<span class="tag">${escapeHTML(skill)}</span>`).join("")
          : `<span class="tag">No missing skills listed</span>`
        }
      </div>

      <h3 class="sub" style="margin-top:1.5rem">Skill Progression Roadmap</h3>
      <p style="font-size:0.8rem;color:var(--text-muted,#8899a6);margin:-0.4rem 0 0.8rem">
        ${pathsExplored > 0 ? `Optimal route selected from ${pathsExplored} explored combinations — ordered by lowest learning cost` : "Optimal route selected by Dijkstra algorithm"}
      </p>

      <div class="pref-list">
        ${(() => {
          if (!sortedPath.length) return `<p class="muted">No roadmap steps found.</p>`;
          let runningScore = data.start_score || 0;
          const maxImprovement = Math.max(...sortedPath.map(s => s.improvement || 0));
          return sortedPath.map((step, i) => {
            const isFirst = i === 0;
            runningScore += step.improvement || 0;
            const barWidth = maxImprovement > 0
              ? Math.round((step.improvement / maxImprovement) * 100)
              : 100;
            return `
            <div class="pref" style="
              border-left: 3px solid ${isFirst ? '#2dc4b3' : '#1a8a7a'};
              padding-left: 0.75rem;
              opacity: ${Math.max(0.6, 1 - i * 0.08)};
              max-width: 100%;
              box-sizing: border-box;
            ">
              <span class="dot dot-1"></span>
              <div style="width:100%">
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <p style="margin:0"><strong>Step ${i + 1}:</strong> Learn ${escapeHTML(step.learn)}</p>
                  <span style="
                    font-size:0.78rem;font-weight:700;color:#2dc4b3;
                    background:rgba(45,196,179,0.1);padding:2px 8px;
                    border-radius:12px;white-space:nowrap;margin-left:0.5rem;
                  ">+${Math.round(step.improvement || 0)}%</span>
                </div>
                <div style="height:4px;background:rgba(45,196,179,0.15);border-radius:2px;margin:6px 0 4px;">
                  <div style="height:4px;width:${barWidth}%;background:linear-gradient(90deg,#2dc4b3,#1ea899);border-radius:2px;"></div>
                </div>
                <small style="color:var(--text-muted,#8899a6)">
                  Score after: ${Math.round(runningScore)}%
                  ${isFirst ? '&nbsp;·&nbsp;<span style="color:#2dc4b3">Start here — lowest cost, highest efficiency</span>' : ''}
                </small>
              </div>
            </div>
          `}).join("");
        })()}
      </div>

      <button class="btn primary-btn" style="margin-top:1.5rem" onclick="loadCourses(${jobId})">
        Find Courses
      </button>
    `;

    panel.scrollIntoView({ behavior:"smooth" });

  }catch(error){
    panel.innerHTML = `<p class="muted">Could not connect to backend.</p>`;
    logApi("GUIDANCE ERROR", { error:error.message });
  }
}

// ===============================
// COURSE RECOMMENDATIONS
// ===============================
async function loadCourses(jobId){
  const panel = document.getElementById("guidancePanel");

  if(!panel) return;

  try{
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/guidance-courses`, {
      headers:authHeaders()
    });

    const data = await res.json();

    logApi("COURSES RESPONSE", data);

    // const courses = data.courses || data.recommendations || [];

    const courses = data.courses || [];
    const aiMessage = data.message || "Recommended courses for your path:";

    // panel.innerHTML += `
    //   <h3 class="sub">Recommended Courses</h3>

    //   <div class="pref-list">
    //     ${
    //       courses.length
    //       ? courses.map(course => `
    //         <div class="pref">
    //           <span class="dot dot-3"></span>
    //           <div>
    //             <p>${escapeHTML(course.title || course.name || "Course")}</p>
    //             <small>${escapeHTML(course.platform || course.provider || "Kaggle / External")}</small>
    //           </div>
    //         </div>
    //       `).join("")
    //       : `<p class="muted">No course recommendations returned yet.</p>`
    //     }
    //   </div>
    // `;

    // AI Agent response
    panel.innerHTML = `
      <div class="ai-guidance-intro">
        <p class="lede-sm">${escapeHTML(aiMessage)}</p>
      </div>
      <h3 class="sub">Learning Path</h3>
      <div class="course-grid">
        ${
          courses.length
          ? courses.map(course => `
            <div class="pref">
              <span class="dot dot-3"></span>
              <div>
                <strong>${escapeHTML(course.name)}</strong>
                <p class="small muted">${escapeHTML(course.guidance_note)}</p>
                <a href="${course.link}" target="_blank" class="course-link">
                   ${escapeHTML(course.phrase)}
                </a>
              </div>
            </div>
          `).join("")
          : `<p class="muted">No specific courses found for these skills.</p>`
        }
      </div>
    `;

  }catch(error){
    logApi("COURSES ERROR", { error:error.message });
  }
}


// ===============================
// BOOKMARK JOB
// ===============================
async function bookmarkJob(jobId){
  try{
    const res = await fetch(`${API_BASE}/api/bookmarks`, {
      method:"POST",
      headers:{
        ...authHeaders(),
        "Content-Type":"application/json"
      },
      body:JSON.stringify({
        job_id:jobId
      })
    });

    const data = await res.json().catch(() => ({}));

    logApi("BOOKMARK RESPONSE", data);

    if(res.ok){
      showFlash("Job bookmarked successfully!");
      await loadBookmarks();
    }else{
      showFlash(data.msg || data.error || "Could not bookmark job.", "error");
    }

  }catch(error){
    alert("Could not connect to backend.");
    logApi("BOOKMARK ERROR", { error:error.message });
  }
}


async function loadBookmarks(){
  const box = document.getElementById("bookmarkList");

  if(!box) return;

  try{
    const res = await fetch(`${API_BASE}/api/bookmarks`, {
      headers:authHeaders()
    });

    const data = await res.json();

    logApi("BOOKMARKS RESPONSE", data);

    const bookmarks = data.bookmarks || data.jobs || data;

    if(!Array.isArray(bookmarks) || !bookmarks.length){
      box.innerHTML = `<p class="muted">No bookmarks yet.</p>`;
      return;
    }

    box.innerHTML = bookmarks.map(job => {
      const jobId = getJobId(job);

      return `
        <div class="job-card">
          <h3>${escapeHTML(job.title || "Saved Job")}</h3>
          <p class="muted">${escapeHTML(job.company || "Unknown Company")}</p>

          <div class="job-actions">
            <button class="btn ghost-btn" onclick="runGuidance(${jobId})">
              Guidance Mode
            </button>

            <button class="btn primary-btn" onclick="removeBookmark(${jobId})">
              Remove
            </button>
          </div>
        </div>
      `;
    }).join("");

  }catch(error){
    box.innerHTML = `<p class="muted">Could not load bookmarks.</p>`;
    logApi("BOOKMARKS ERROR", { error:error.message });
  }
}


async function removeBookmark(jobId){
  try{
    const res = await fetch(`${API_BASE}/api/bookmarks/${jobId}`, {
      method:"DELETE",
      headers:authHeaders()
    });

    const data = await res.json().catch(() => ({}));

    logApi("REMOVE BOOKMARK RESPONSE", data);

    await loadBookmarks();

  }catch(error){
    logApi("REMOVE BOOKMARK ERROR", { error:error.message });
  }
}


// ===============================
// DASHBOARD & AUTH STATE CONTROL
// ===============================
window.addEventListener("DOMContentLoaded", async () => {
  const dashboard = document.getElementById("dashboard");
  const token = getToken();
  const storedName = localStorage.getItem("ys_user_name");

  if(dashboard){
    if(!token){
      window.location.href = "/register";
      return;
    }

    dashboard.classList.remove("hidden");

    const nameBox = document.getElementById("currentUserName");
    if(nameBox && storedName){
      nameBox.textContent = storedName;
    }

    await loadSavedResume();
    await loadMatches();
    await loadBookmarks();
  }

  if(token){
    console.log("User is logged in as:", storedName);
  }
});