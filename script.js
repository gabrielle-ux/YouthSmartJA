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

if(navToggle){
  navToggle.addEventListener("click", () => {
    navLinks.classList.toggle("open");
  });
}

document.querySelectorAll(".nav-links a").forEach(link => {
  link.addEventListener("click", () => {
    navLinks.classList.remove("open");
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
window.addEventListener("load", revealOnScroll);


// ===============================
// ACTIVE NAVIGATION LINK
// ===============================
const sections = document.querySelectorAll("section[id]");
const navItems = document.querySelectorAll(".nav-links a");

function activateNavLink(){
  let currentSection = "";

  sections.forEach(section => {
    const sectionTop = section.offsetTop - 200;
    const sectionHeight = section.offsetHeight;

    if(
      window.scrollY >= sectionTop &&
      window.scrollY < sectionTop + sectionHeight
    ){
      currentSection = section.getAttribute("id");
    }
  });

  navItems.forEach(link => {
    link.classList.remove("active");

    if(link.getAttribute("href") === `#${currentSection}`){
      link.classList.add("active");
    }
  });
}

window.addEventListener("scroll", activateNavLink);


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

    document.getElementById(formId).classList.add("active");
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
      full_name: document.getElementById("registerName").value,
      email: document.getElementById("registerEmail").value,
      password: document.getElementById("registerPassword").value,
      role: document.getElementById("registerRole").value
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

      showMessage("Account created. Now login.");
      document.querySelector('[data-tab="login"]').click();

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
      email: document.getElementById("loginEmail").value,
      password: document.getElementById("loginPassword").value
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
      showDashboard();

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

    hideDashboard();

    window.scrollTo({
      top:0,
      behavior:"smooth"
    });
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

    if(!fileInput.files.length){
      alert("Choose a resume first.");
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

      renderSkillTags(data.keywords || data.skills || data.resume_keywords || []);
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
    .map(skill => `<span class="tag">${skill}</span>`)
    .join("");
}


// ===============================
// PREFERENCES
// ===============================
const savePrefsBtn = document.getElementById("savePrefsBtn");

if(savePrefsBtn){
  savePrefsBtn.addEventListener("click", () => {
    const jobType = document.getElementById("jobTypePref").value;
    const location = document.getElementById("locationPref").value;

    localStorage.setItem("ys_pref_job_type", jobType);
    localStorage.setItem("ys_pref_location", location);

    alert("Preferences saved.");
    loadMatches();
  });
}


// ===============================
// JOB SEARCH
// ===============================
const searchJobsBtn = document.getElementById("searchJobsBtn");

if(searchJobsBtn){
  searchJobsBtn.addEventListener("click", async () => {
    const query = document.getElementById("jobSearchInput").value || "software";

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
  const jobTypePref = localStorage.getItem("ys_pref_job_type") || "";
  const locationPref = localStorage.getItem("ys_pref_location") || "";

  let score = 0.5;

  const text = `
    ${job.title || ""}
    ${job.description || ""}
    ${job.job_type || ""}
    ${job.city || ""}
    ${job.location || ""}
  `.toLowerCase();

  if(jobTypePref && text.includes(jobTypePref.toLowerCase())){
    score += 0.25;
  }

  if(locationPref && text.includes(locationPref.toLowerCase())){
    score += 0.25;
  }

  return Math.min(score, 1);
}


function getJobCategory(matchScore, prefScore){
  if(prefScore >= 75 && matchScore >= 75){
    return "High Preference + High Match";
  }

  if(prefScore >= 75 && matchScore < 75){
    return "High Preference + Low Match";
  }

  if(prefScore < 75 && matchScore >= 75){
    return "Low Preference + High Match";
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
        <h3>${job.title || "Untitled Job"}</h3>

        <p class="muted">
          ${job.company || "Unknown Company"}
          ·
          ${job.city || job.location || job.country || "Jamaica"}
        </p>

        <div class="score-row">
          <span class="score-pill">Match ${match}%</span>
          <span class="score-pill">Preference ${pref}%</span>
          <span class="score-pill">Final ${finalScore}%</span>
          <span class="category-pill">${category}</span>
        </div>

        <p class="muted small">
          ${job.description ? job.description.slice(0,180) + "..." : "No description available."}
        </p>

        <div class="job-actions">
          ${
            jobLink
            ? `
              <a href="${jobLink}" target="_blank" class="btn primary-btn">
                Apply Now
              </a>
            `
            : ""
          }

          <button class="btn ghost-btn" onclick="viewJobDetails(${job.id})">
            View Details
          </button>

          <button class="btn ghost-btn" onclick="runGuidance(${job.id})">
            Guidance Mode
          </button>

          <button class="btn primary-btn" onclick="bookmarkJob(${job.id})">
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

    const job = await res.json();

    logApi("JOB DETAILS RESPONSE", job);

    if(!res.ok){
      panel.innerHTML = `<p class="muted">Could not load job details.</p>`;
      return;
    }

    const jobLink = getJobLink(job);

    panel.innerHTML = `
      <h3>${job.title || "Job Details"}</h3>

      <p class="muted">
        ${job.company || "Unknown Company"}
        ·
        ${job.city || job.location || job.country || "Jamaica"}
      </p>

      <p style="margin-top:1rem;">
        ${job.description || "No description available."}
      </p>

      <div class="job-actions" style="margin-top:1.5rem;">
        ${
          jobLink
          ? `
            <a href="${jobLink}" target="_blank" class="btn primary-btn">
              Apply Externally
            </a>
          `
          : ""
        }

        <button class="btn ghost-btn" onclick="runGuidance(${job.id})">
          Guidance Mode
        </button>

        <button class="btn primary-btn" onclick="bookmarkJob(${job.id})">
          Bookmark
        </button>
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

    const path = data.path || [];
    const missingSkills = data.missing_skills || [];

    panel.innerHTML = `
      <h3>${data.job?.title || "Career Roadmap"}</h3>

      <div class="score-row">
        <span class="score-pill">Start ${Math.round(data.start_score || 0)}%</span>
         <span class="score-pill">Final ${Math.round(data.final_score || 0)}%</span>
        <span class="score-pill">${data.reached_target ? "Target Reached" : "Keep Improving"}</span>
      </div>

      <h3 class="sub">Missing Skills</h3>

      <div class="tag-list">
        ${
          missingSkills.length
          ? missingSkills.map(skill => `<span class="tag">${skill}</span>`).join("")
          : `<span class="tag">No missing skills listed</span>`
        }
      </div>

      <h3 class="sub">Learning Roadmap</h3>

      <div class="pref-list">
        ${
          path.length
          ? path.map(step => `
            <div class="pref">
              <span class="dot dot-1"></span>
              <div>
                <p>Learn ${step.learn}</p>
                <small>
                  Improvement:
                  ${Math.round(step.improvement || 0)}%
                 · Score:
                  ${Math.round(step.score || 0)}%
                </small>
              </div>
            </div>
          `).join("")
          : `<p class="muted">No roadmap steps found.</p>`
        }
      </div>

      <button class="btn primary-btn" onclick="loadCourses(${jobId})">
        Find Courses
      </button>
    `;

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

  try{
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/guidance-courses`, {
      headers:authHeaders()
    });

    const data = await res.json();

    logApi("COURSES RESPONSE", data);

    const courses = data.courses || data.recommendations || [];

    panel.innerHTML += `
      <h3 class="sub">Recommended Courses</h3>

      <div class="pref-list">
        ${
          courses.length
          ? courses.map(course => `
            <div class="pref">
              <span class="dot dot-3"></span>
              <div>
                <p>${course.title || course.name || "Course"}</p>
                <small>${course.platform || course.provider || "Kaggle / External"}</small>
              </div>
            </div>
          `).join("")
          : `<p class="muted">No course recommendations returned yet.</p>`
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
      alert("Job bookmarked.");
      await loadBookmarks();
    }else{
      alert(data.msg || data.error || "Could not bookmark job.");
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

    box.innerHTML = bookmarks.map(job => `
      <div class="job-card">
        <h3>${job.title || "Saved Job"}</h3>
        <p class="muted">${job.company || "Unknown Company"}</p>

        <div class="job-actions">
          <button class="btn ghost-btn" onclick="runGuidance(${job.id || job.job_id})">
            Guidance Mode
          </button>

          <button class="btn primary-btn" onclick="removeBookmark(${job.id || job.job_id})">
            Remove
          </button>
        </div>
      </div>
    `).join("");

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
// RESTORE LOGIN STATE
// ===============================
window.addEventListener("load", () => {
  const token = getToken();
  const userName = localStorage.getItem("ys_user_name");

  if(token){
    const nameBox = document.getElementById("currentUserName");

    if(nameBox && userName){
      nameBox.textContent = userName;
    }

    showDashboard();
    loadMatches();
    loadBookmarks();
  }
});