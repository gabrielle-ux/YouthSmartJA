// ===============================
// CONFIG
// ===============================
const API_BASE = "http://127.0.0.1:5000";

function getToken(){
  return localStorage.getItem("ys_token");
}

function authHeaders(){
  const token = getToken();
  return token ? { "Authorization": `Bearer ${token}` } : {};
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
  if(box){ box.textContent = message; }
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
  if(dashboard){ dashboard.classList.add("hidden"); }
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
    if(rect.top < triggerBottom){ el.classList.add("in"); }
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
    blob.style.transform = `translate(${(x - 0.5) * speed}px, ${(y - 0.5) * speed}px)`;
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
  position:"fixed", bottom:"20px", right:"20px",
  width:"50px", height:"50px", borderRadius:"50%",
  border:"none", background:"linear-gradient(135deg,#2dc4b3,#1ea899)",
  color:"#0f1a1f", fontSize:"1.2rem", fontWeight:"bold",
  cursor:"pointer", opacity:"0", pointerEvents:"none",
  transition:"all .3s ease", zIndex:"9999",
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
  window.scrollTo({ top:0, behavior:"smooth" });
});


// ===============================
// AUTH TABS
// ===============================
document.querySelectorAll(".auth-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".auth-tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".auth-form").forEach(f => f.classList.remove("active"));
    tab.classList.add("active");
    const formId = tab.dataset.tab === "login" ? "loginForm" : "registerForm";
    const form = document.getElementById(formId);
    if(form){ form.classList.add("active"); }
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
      full_name:          document.getElementById("registerName")?.value?.trim() || "",
      email:              document.getElementById("registerEmail")?.value?.trim() || "",
      password:           document.getElementById("registerPassword")?.value || "",
      role:               document.getElementById("registerRole")?.value || "student",
      career_interest:    document.getElementById("careerInterest")?.value?.trim() || "",
      preferred_job_type: document.getElementById("preferredJobType")?.value || "",
      work_style:         document.getElementById("workStyle")?.value || "",
      availability:       document.getElementById("availability")?.value || "",
    };

    try{
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
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
      if(loginTab){ loginTab.click(); }

    }catch(error){
      showMessage("Could not connect to backend.");
      logApi("REGISTER ERROR", { error:error.message });
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
      email:    document.getElementById("loginEmail")?.value || "",
      password: document.getElementById("loginPassword")?.value || ""
    };

    try{
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body:JSON.stringify(payload)
      });

      const data = await res.json();
      logApi("LOGIN RESPONSE", data);

      if(!res.ok){
        showMessage(data.msg || data.error || "Login failed");
        return;
      }

      const token = data.access_token || data.token;
      if(token){ localStorage.setItem("ys_token", token); }

      const userName =
        data.user?.full_name || data.user?.name ||
        data.full_name || data.name ||
        data.email || payload.email;

      localStorage.setItem("ys_user_name", userName);

      const nameBox = document.getElementById("currentUserName");
      if(nameBox){ nameBox.textContent = userName; }

      showMessage("Login successful.");
      setTimeout(() => { window.location.href = "/dashboard"; }, 1000);

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

    if(status){ status.textContent = "Uploading and processing resume..."; }

    try{
      const res = await fetch(`${API_BASE}/api/resume/upload`, {
        method:"POST",
        headers:authHeaders(),
        body:formData
      });

      const data = await res.json();
      logApi("RESUME UPLOAD RESPONSE", data);

      if(!res.ok){
        if(status){ status.textContent = data.msg || data.error || "Resume upload failed."; }
        return;
      }

      if(status){ status.textContent = "Resume uploaded successfully."; }

      await loadSavedResume();
      await loadMatches();

    }catch(error){
      if(status){ status.textContent = "Could not connect to backend."; }
      logApi("RESUME UPLOAD ERROR", { error:error.message });
    }
  });
}


function renderSkillTags(skills){
  const box = document.getElementById("skillTags");
  if(!box) return;

  if(typeof skills === "string"){
    skills = skills.split(",").map(skill => skill.trim()).filter(Boolean);
  }

  if(!Array.isArray(skills)){ skills = []; }

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
  if(!getToken()) return;

  try{
    const res = await fetch(`${API_BASE}/api/resume/me`, { headers:authHeaders() });
    const data = await res.json();
    logApi("SAVED RESUME RESPONSE", data);

    if(!res.ok || !data.ok){
      if(status){ status.textContent = "Could not check saved resume."; }
      return;
    }

    if(!data.has_resume){
      if(status){ status.textContent = "No resume uploaded yet."; }
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
    if(status){ status.textContent = "Could not connect to backend."; }
    logApi("SAVED RESUME ERROR", { error:error.message });
  }
}


// ===============================
// PREFERENCES & SIDEBAR CONTROL
// ===============================
const filterSidebar  = document.getElementById("filterSidebar");
const sidebarOverlay = document.getElementById("sidebarOverlay");
const openFilterBtn  = document.getElementById("openFilterBtn");
const closeFilterBtn = document.getElementById("closeFilterBtn");
const savePrefsBtn   = document.getElementById("savePrefsBtn");

const hideSidebar = () => {
  if(filterSidebar)  filterSidebar.classList.remove("active");
  if(sidebarOverlay) sidebarOverlay.classList.remove("active");
};

if(openFilterBtn){
  openFilterBtn.addEventListener("click", () => {
    filterSidebar.classList.add("active");
    sidebarOverlay.classList.add("active");
  });
}

if(closeFilterBtn) closeFilterBtn.addEventListener("click", hideSidebar);
if(sidebarOverlay) sidebarOverlay.addEventListener("click", hideSidebar);


// ===============================
// GET ACTIVE FILTERS
// ===============================
function getActiveFilters(){
  const jobType = document.getElementById("jobTypePref")?.value
               || document.getElementById("preferredJobType")?.value
               || localStorage.getItem("ys_pref_job_type")
               || "";

  const workStyle = document.getElementById("workStylePref")?.value
                 || document.getElementById("workStyle")?.value
                 || localStorage.getItem("ys_pref_work_style")
                 || "";

  const location = document.getElementById("locationPref")?.value
                || localStorage.getItem("ys_pref_location")
                || "";

  const availability = document.getElementById("availabilityPref")?.value
                    || document.getElementById("availability")?.value
                    || localStorage.getItem("ys_pref_availability")
                    || "";

  let typeParam = jobType.toLowerCase();
  if(workStyle.toLowerCase() === "remote"){
    typeParam = "remote";
  } else if(workStyle.toLowerCase() === "on-site" || workStyle.toLowerCase() === "onsite"){
    typeParam = "onsite";
  } else if(workStyle.toLowerCase() === "hybrid"){
    typeParam = "";
  }

  return { jobType, workStyle, location, availability, typeParam };
}


// ===============================
// BUILD SEARCH URL
// ===============================
function buildSearchUrl(keyword = ""){
  const { typeParam, location } = getActiveFilters();

  const params = new URLSearchParams();

  if(keyword) params.set("q", keyword);
  if(typeParam && typeParam !== "preferred job type") params.set("type", typeParam);
  if(location) params.set("location", location);
  if(!location) params.set("country", "jm");
  params.set("limit", "20");

  return `${API_BASE}/api/jobs/search?${params.toString()}`;
}


if(savePrefsBtn){
  savePrefsBtn.addEventListener("click", () => {
    const { jobType, workStyle, location, availability } = getActiveFilters();

    localStorage.setItem("ys_pref_job_type",     jobType);
    localStorage.setItem("ys_pref_work_style",   workStyle);
    localStorage.setItem("ys_pref_location",     location);
    localStorage.setItem("ys_pref_availability", availability);

    showFlash("Preferences saved! Refreshing jobs...");
    hideSidebar();

    const currentKeyword = document.getElementById("jobSearchInput")?.value?.trim() || "";
    loadFilteredJobs(currentKeyword);
  });
}


// ===============================
// LOAD FILTERED JOBS
// ===============================
async function loadFilteredJobs(keyword = ""){
  const feed = document.getElementById("jobFeed");
  if(!feed) return;

  feed.innerHTML = `<p class="muted">Loading jobs...</p>`;

  const url = buildSearchUrl(keyword);

  try{
    const res = await fetch(url, { headers:authHeaders() });
    const data = await res.json();

    logApi("FILTERED JOBS RESPONSE", data);

    if(!res.ok){
      feed.innerHTML = `<p class="muted">Could not load jobs. Showing resume matches instead.</p>`;
      await loadMatches();
      return;
    }

    const jobs = data.jobs || data.results || [];
    renderJobs(Array.isArray(jobs) ? jobs : []);

  }catch(error){
    logApi("FILTERED JOBS ERROR", { error:error.message });
    feed.innerHTML = `<p class="muted">Could not connect to backend.</p>`;
  }
}


// ===============================
// JOB SEARCH BUTTON
// ===============================
const searchJobsBtn = document.getElementById("searchJobsBtn");

if(searchJobsBtn){
  searchJobsBtn.addEventListener("click", () => {
    const query = document.getElementById("jobSearchInput")?.value?.trim() || "";
    loadFilteredJobs(query);
  });
}

const jobSearchInput = document.getElementById("jobSearchInput");
if(jobSearchInput){
  jobSearchInput.addEventListener("keydown", (e) => {
    if(e.key === "Enter"){
      loadFilteredJobs(jobSearchInput.value.trim());
    }
  });
}


// ===============================
// LOAD MATCHES (resume-based fallback)
// ===============================
async function loadMatches(){
  const feed = document.getElementById("jobFeed");
  if(!feed) return;

  feed.innerHTML = `<p class="muted">Loading matched jobs...</p>`;

  try{
    const res = await fetch(`${API_BASE}/api/jobs/matches`, { headers:authHeaders() });
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
  const { jobType, workStyle, availability } = getActiveFilters();

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

  if(jobType     && text.includes(jobType.toLowerCase()))       score += 0.40;
  if(workStyle   && text.includes(workStyle.toLowerCase()))     score += 0.30;
  if(availability && text.includes(availability.toLowerCase())) score += 0.30;

  return Math.min(score, 1);
}


function getJobCategory(matchScore, prefScore){
  if(prefScore >= 50 && matchScore >= 25) return "Strong Preference + Good Match";
  if(prefScore >= 50)                     return "Strong Preference + Needs Skills";
  if(matchScore >= 25)                    return "Good Match + Low Preference";
  return "Low Preference + Low Match";
}

function filterJobsByResume(jobs){
  return jobs
    .map(job => {
      const match = computeMatchScore(job);
      return { ...job, match_score: match };
    })
    .filter(job => job.match_score >= 0.25); // strict filter
}

function renderJobs(jobs){
  const feed = document.getElementById("jobFeed");
  if(!feed) return;

  // Sort highest match score first
  jobs = [...jobs].sort((a, b) => {
    const scoreA = a.match_score ?? a.similarity ?? a.score ?? 0;
    const scoreB = b.match_score ?? b.similarity ?? b.score ?? 0;
    return scoreB - scoreA;
  });

  if(!jobs.length){
    feed.innerHTML = `<p class="muted">No jobs found. Try a different search or adjust your filters.</p>`;
    updateCareerReadiness(0);
    return;
  }

  let totalFinal = 0;

  const html = jobs.map(job => {
    const jobId = getJobId(job);

    const rawMatch = job.match_score ?? job.similarity ?? job.score ?? 0;
    const match = rawMatch <= 1 ? Math.round(rawMatch * 100) : Math.round(rawMatch);

    const prefRaw = job.preference_score ?? calculatePreferenceScore(job);
    const pref = prefRaw <= 1 ? Math.round(prefRaw * 100) : Math.round(prefRaw);

    const finalScore = Math.round((match + pref) / 2);
    totalFinal += finalScore;

    const category = getJobCategory(match, pref);
    const jobLink  = getJobLink(job);

    return `
      <div class="job-card">
        <h3>${escapeHTML(job.title || "Untitled Job")}</h3>
        <p class="muted">
          ${escapeHTML(job.company || "Unknown Company")}
          ·
          ${escapeHTML(job.city || job.location || job.country || "Jamaica")}
          ${job.is_remote ? ' · <span style="color:#2dc4b3">Remote</span>' : ""}
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
          ${jobLink ? `<a href="${escapeHTML(jobLink)}" target="_blank" class="btn primary-btn">Apply Now</a>` : ""}
          <a href="/jobs/${jobId}" class="btn ghost-btn">View Details</a>
          <button class="btn ghost-btn"   onclick="runGuidance(${jobId})">Guidance Mode</button>
          <button class="btn primary-btn" onclick="bookmarkJob(${jobId})">Bookmark</button>
        </div>
      </div>
    `;
  }).join("");

  feed.innerHTML = html;
  updateCareerReadiness(Math.round(totalFinal / jobs.length));
}

function updateCareerReadiness(score){
  const box = document.getElementById("careerReadiness");
  if(box){ box.textContent = `${score || "--"}%`; }
}


// ===============================
// GUIDANCE HELPERS
// ===============================
const SOFT_SKILLS_FRONTEND = new Set([
  "communication", "teamwork", "attention to detail", "problem solving",
  "leadership", "time management", "critical thinking", "adaptability",
  "professionalism", "organization", "public speaking", "presentation",
  "research", "writing", "word", "microsoft office",
  "english", "documentation", "physics", "biology", "chemistry",
  "mathematics", "filing", "scheduling", "record keeping",
  "software engineering", "full stack", "dashboard", "reporting",
  "digital marketing", "social media", "content creation", "seo",
  "branding", "copywriting", "email marketing", "campaign management",
  "customer service", "sales", "retail", "cashier", "call center",
  "phone etiquette", "hospitality", "food service", "bartending",
  "housekeeping", "front desk", "tourism", "guest service",
  "accounting", "bookkeeping", "payroll", "invoicing",
  "teaching", "tutoring", "lesson planning", "classroom management",
  "patient care", "caregiving", "first aid", "healthcare support",
]);

function filterSoftSkills(steps){
  return steps.filter(step => !SOFT_SKILLS_FRONTEND.has((step.learn || "").toLowerCase()));
}

function filterSoftSkillTags(skills){
  return skills.filter(s => !SOFT_SKILLS_FRONTEND.has((s || "").toLowerCase()));
}

function isSoftwareJob(jobTitle){
  const techTerms = ["developer", "engineer", "software", "backend", "frontend",
                     "data", "devops", "cloud", "web", "fullstack", "full stack", "programmer"];
  return techTerms.some(term => (jobTitle || "").toLowerCase().includes(term));
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

    const rawPath       = data.path || [];
    const rawMissing    = data.missing_skills || [];
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
      <div style="margin:1rem 0;padding:0.75rem 1rem;background:rgba(13,122,95,0.08);border-left:3px solid #2dc4b3;border-radius:6px;font-size:0.82rem;color:var(--text-muted,#8899a6);">
        Dijkstra explored <strong style="color:#2dc4b3">${pathsExplored} skill combinations</strong>
        and selected the most efficient learning path
      </div>` : ""}
      <h3 class="sub">Missing Skills</h3>
      <div class="tag-list">
        ${missingSkills.length
          ? missingSkills.map(skill => `<span class="tag">${escapeHTML(skill)}</span>`).join("")
          : `<span class="tag">No missing skills listed</span>`}
      </div>
      <h3 class="sub" style="margin-top:1.5rem">Skill Progression Roadmap</h3>
      <p style="font-size:0.8rem;color:var(--text-muted,#8899a6);margin:-0.4rem 0 0.8rem">
        ${pathsExplored > 0
          ? `Optimal route selected from ${pathsExplored} explored combinations`
          : "Optimal route selected by Dijkstra algorithm"}
      </p>
      <div class="pref-list">
        ${(() => {
          if(!sortedPath.length) return `<p class="muted">No roadmap steps found.</p>`;
          let runningScore = data.start_score || 0;
          const maxImprovement = Math.max(...sortedPath.map(s => s.improvement || 0));
          return sortedPath.map((step, i) => {
            const isFirst = i === 0;
            runningScore += step.improvement || 0;
            const barWidth = maxImprovement > 0
              ? Math.round((step.improvement / maxImprovement) * 100)
              : 100;
            return `
            <div class="pref" style="border-left:3px solid ${isFirst ? '#2dc4b3' : '#1a8a7a'};padding-left:0.75rem;opacity:${Math.max(0.6, 1 - i * 0.08)};max-width:100%;box-sizing:border-box;">
              <span class="dot dot-1"></span>
              <div style="width:100%">
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <p style="margin:0"><strong>Step ${i + 1}:</strong> Learn ${escapeHTML(step.learn)}</p>
                  <span style="font-size:0.78rem;font-weight:700;color:#2dc4b3;background:rgba(45,196,179,0.1);padding:2px 8px;border-radius:12px;white-space:nowrap;margin-left:0.5rem;">
                    +${Math.round(step.improvement || 0)}%
                  </span>
                </div>
                <div style="height:4px;background:rgba(45,196,179,0.15);border-radius:2px;margin:6px 0 4px;">
                  <div style="height:4px;width:${barWidth}%;background:linear-gradient(90deg,#2dc4b3,#1ea899);border-radius:2px;"></div>
                </div>
                <small style="color:var(--text-muted,#8899a6)">
                  Score after: ${Math.round(runningScore)}%
                  ${isFirst ? ' &nbsp;·&nbsp; <span style="color:#2dc4b3">Start here</span>' : ''}
                </small>
              </div>
            </div>`;
          }).join("");
        })()}
      </div>
      <div id="courseSection">
        <button id="loadCoursesBtn" class="btn primary-btn" style="margin-top:1.5rem" onclick="loadCourses(${jobId})">
          Find Courses
        </button>
      </div>
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
  const courseSection = document.getElementById("courseSection");
  if(!courseSection) return;

  courseSection.innerHTML = `<p class="muted">Fetching course recommendations...</p>`;

  try{
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/guidance-courses`, { headers:authHeaders() });
    const data = await res.json();
    logApi("COURSES RESPONSE", data);

    if(!res.ok || data.ok === false){
      courseSection.innerHTML = `<p class="muted">Error: ${data.error || "Could not load courses."}</p>`;
      return;
    }

    const courses   = data.courses || [];
    const aiMessage = data.message || "Recommended courses for your path:";

    courseSection.innerHTML = `
      <div class="ai-guidance-intro">
        <h3 class="sub">Course Recommendations</h3>
        <p class="lede-sm">${escapeHTML(aiMessage)}</p>
      </div>
      <h3 class="sub">Learning Path</h3>
      <div class="course-grid">
        ${courses.length
          ? courses.map(course => `
            <div class="pref">
              <span class="dot dot-3"></span>
              <div>
                <strong>${escapeHTML(course.name)}</strong>
                <p class="small muted">${escapeHTML(course.guidance_note || "")}</p>
                <a href="${course.link}" target="_blank" class="course-link">${escapeHTML(course.phrase || "View Course")}</a>
              </div>
            </div>`).join("")
          : `<p class="muted">No specific courses found for these skills.</p>`}
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
      headers:{ ...authHeaders(), "Content-Type":"application/json" },
      body:JSON.stringify({ job_id:jobId })
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
    const res = await fetch(`${API_BASE}/api/bookmarks`, { headers:authHeaders() });
    const data = await res.json();
    logApi("BOOKMARKS RESPONSE", data);

    const bookmarks = data.bookmarks || data.jobs || data;

    if(!Array.isArray(bookmarks) || !bookmarks.length){
      box.innerHTML = `<p class="muted">No bookmarks yet.</p>`;
      return;
    }

    box.innerHTML = bookmarks.map(job => {
      const jobId = job.job_id || job.id;
      return `
        <div class="job-card">
          <h3>${escapeHTML(job.title || "Saved Job")}</h3>
          <p class="muted">${escapeHTML(job.company || "Unknown Company")}</p>
          <div class="job-actions">
            <a href="/jobs/${jobId}" class="btn ghost-btn">View Details</a>
            <button class="btn ghost-btn"   onclick="runGuidance(${jobId})">Guidance Mode</button>
            <button class="btn primary-btn" onclick="removeBookmark(${jobId})">Remove</button>
          </div>
        </div>`;
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
  const token      = getToken();
  const storedName = localStorage.getItem("ys_user_name");

  // 1. GLOBAL AUTH CHECK
  // Public pages + /jobs/* detail pages don't redirect to login.
  const publicPages = ["/register", "/", "/about"];
  const isPublic = publicPages.includes(window.location.pathname)
                || window.location.pathname.startsWith("/jobs/");

  if(!token){
    if(!isPublic){
      window.location.href = "/register";
    }
    return;
  }

  // 2. DASHBOARD PAGE LOGIC
  const dashboard = document.getElementById("dashboard");
  if(dashboard){
    dashboard.classList.remove("hidden");
    const nameBox = document.getElementById("currentUserName");
    if(nameBox && storedName) nameBox.textContent = storedName;
    await loadSavedResume();
  }

  // 3. JOBS PAGE LOGIC
  const jobFeed = document.getElementById("jobFeed");
  if(jobFeed){
    await loadFilteredJobs("");
  }

  // 4. BOOKMARKS — runs on ANY page that has a bookmarkList element
  if(document.getElementById("bookmarkList")){
    await loadBookmarks();
  }
});
