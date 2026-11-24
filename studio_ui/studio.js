    (function () {
      const hologramCanvas = document.getElementById('hologramCanvas');
      const waveformCanvas = document.getElementById('waveformCanvas');
      const hCtx = hologramCanvas.getContext('2d');
      const wCtx = waveformCanvas.getContext('2d');

      const sidebarStatusText = document.getElementById('sidebarStatusText');
      const sidebarStatusBadge = document.getElementById('sidebarStatusBadge');
      const sidebarStatusDot = document.getElementById('sidebarStatusDot');
      const hologramStateTelemetry = document.getElementById('hologramStateTelemetry');
      const liveCaption = document.getElementById('liveCaption');
      const toneMetrics = document.getElementById('toneMetrics');
      const micSourceLabel = document.getElementById('micSourceLabel');

      const micToggleBtn = document.getElementById('micToggleBtn');
      const micIcon = document.getElementById('micIcon');
      const micBtnTitle = document.getElementById('micBtnTitle');
      const liveMicBtn = document.getElementById('liveMicBtn');
      const pulseTestBtn = document.getElementById('pulseTestBtn');
      const modeButtons = document.querySelectorAll('.mode-btn');

      const chatFeed = document.getElementById('chatFeed');
      const chatForm = document.getElementById('chatForm');
      const chatInput = document.getElementById('chatInput');
      const clearChatBtn = document.getElementById('clearChatBtn');
      const turnCountLabel = document.getElementById('turnCountLabel');

let currentMode="standby", time=0;
      const modeConfig = {
        listening: {
          label: 'LISTENING',
          primary: '#4CD7F6',
          secondary: '#A1CEDB',
          glow: 'rgba(76, 215, 246, 0.28)',
        },
        speaking: {
          label: 'SPEAKING',
          primary: '#34D399',
          secondary: '#4CD7F6',
          glow: 'rgba(52, 211, 153, 0.34)',
        },
        thinking: {
          label: 'THINKING',
          primary: '#FFB873',
          secondary: '#4CD7F6',
          glow: 'rgba(255, 184, 115, 0.28)',
        },
        standby: {
          label: 'STANDBY',
          primary: '#869397',
          secondary: '#3D494C',
          glow: 'rgba(134, 147, 151, 0.14)',
        }
      };

      function resizeCanvases() {
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        const hRect = hologramCanvas.parentElement.getBoundingClientRect();
        const hSize = Math.max(1, Math.floor(Math.min(hRect.width, hRect.height)));
        hologramCanvas.style.width = hSize + 'px';
        hologramCanvas.style.height = hSize + 'px';
        hologramCanvas.width = Math.floor(hSize * dpr);
        hologramCanvas.height = Math.floor(hSize * dpr);

        const wRect = waveformCanvas.parentElement.getBoundingClientRect();
        waveformCanvas.width = Math.max(300, Math.floor(wRect.width * dpr));
        waveformCanvas.height = Math.max(64, Math.floor(wRect.height * dpr));
      }
      window.addEventListener('resize', resizeCanvases);
      resizeCanvases();

      // Mode switching
      function setMode(mode) {
        currentMode = mode;
        const cfg = modeConfig[mode];
        sidebarStatusText.textContent = cfg.label;
        sidebarStatusDot.style.background = cfg.primary;

        modeButtons.forEach(btn => {
          const active = btn.dataset.mode === mode;
          if (active) {
            btn.className = 'mode-btn px-gutter-md py-gutter-xs rounded-full font-label text-label-sm border transition-colors duration-state-change ease-state-change bg-light-primary dark:bg-dark-primary text-light-on-primary dark:text-dark-on-primary border-light-primary dark:border-dark-primary';
          } else {
            btn.className = 'mode-btn px-gutter-md py-gutter-xs rounded-full font-label text-label-sm border transition-colors duration-state-change ease-state-change bg-light-surface-container-high dark:bg-dark-surface-container-high text-light-on-surface-variant dark:text-dark-on-surface-variant border-light-outline-variant dark:border-dark-outline-variant hover:border-light-primary dark:hover:border-dark-primary';
          }
        });
      }

      function updateTurnCount() {
        const count = chatFeed.querySelectorAll('article').length;
        turnCountLabel.textContent = count + (count === 1 ? ' TURN' : ' TURNS');
      }

      function appendMessage(role, text) {
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const article = document.createElement('article');
        article.setAttribute('data-component-type', 'card');

        if (role === 'user') {
          article.setAttribute('data-component-id', 'card-outlined');
          article.setAttribute('data-component-variant', 'outlined');
          article.className = 'p-gutter-md rounded-md bg-light-surface-container dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant self-end w-[92%]';
          article.innerHTML = `
            <header class="flex items-center justify-between gap-gutter-sm mb-gutter-xs">
              <h3 data-design-text-token="title-sm" class="font-title text-title-sm text-light-on-surface dark:text-dark-on-surface">You</h3>
              <p data-design-text-token="label-sm" class="font-label text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant tabular-nums">${timeStr}</p>
            </header>
            <div>
              <p data-design-text-token="body-md" class="font-body text-body-md text-light-on-surface dark:text-dark-on-surface text-pretty"></p>
            </div>
          `;
        } else {
          article.setAttribute('data-component-id', 'card-elevated');
          article.setAttribute('data-component-variant', 'elevated');
          article.className = 'p-gutter-md rounded-md bg-light-surface-container-high dark:bg-dark-surface-container-high border border-light-outline-variant dark:border-dark-outline-variant self-start w-[94%]';
          article.innerHTML = `
            <header class="flex items-center justify-between gap-gutter-sm mb-gutter-xs">
              <div class="flex items-center gap-gutter-xs">
                <span class="material-symbols-outlined text-[16px] text-light-primary dark:text-dark-primary">graphic_eq</span>
                <h3 data-design-text-token="title-sm" class="font-title text-title-sm text-light-primary dark:text-dark-primary">CLYDEX</h3>
              </div>
              <p data-design-text-token="label-sm" class="font-label text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant tabular-nums">${timeStr}</p>
            </header>
            <div>
              <p data-design-text-token="body-md" class="font-body text-body-md text-light-on-surface dark:text-dark-on-surface text-pretty"></p>
            </div>
          `;
        }
        article.querySelector('p[data-design-text-token="body-md"]').textContent = text;
        chatFeed.appendChild(article);
        chatFeed.scrollTop = chatFeed.scrollHeight;
        updateTurnCount();
      }

      function drawHologram(audio) {
        const w = hologramCanvas.width;
        const h = hologramCanvas.height;
        const cx = w / 2;
        const cy = h / 2;
        const baseR = Math.min(w, h) * 0.28;
        const cfg = modeConfig[currentMode];

        hCtx.clearRect(0, 0, w, h);

        // 1. Soft atmospheric radial aura
        const auraR = baseR * (1.55 + audio.level * 0.32);
        const auraGrad = hCtx.createRadialGradient(cx, cy, baseR * 0.25, cx, cy, auraR);
        auraGrad.addColorStop(0, cfg.glow);
        auraGrad.addColorStop(0.5, 'rgba(6, 182, 212, 0.06)');
        auraGrad.addColorStop(1, 'rgba(9, 15, 17, 0)');
        hCtx.fillStyle = auraGrad;
        hCtx.beginPath();
        hCtx.arc(cx, cy, auraR, 0, Math.PI * 2);
        hCtx.fill();

        hCtx.save();
        hCtx.translate(cx, cy);

        // 2. Outer crisp circular halo ring
        hCtx.strokeStyle = cfg.primary;
        hCtx.globalAlpha = 0.16 + audio.bass * 0.18;
        hCtx.lineWidth = 1.25;
        hCtx.beginPath();
        hCtx.arc(0, 0, baseR * (1.38 + audio.bass * 0.06), 0, Math.PI * 2);
        hCtx.stroke();

        // 3. Smooth rotating twin orbital arcs (clean futuristic round frame)
        hCtx.save();
        hCtx.rotate(time * 0.32);
        hCtx.strokeStyle = cfg.secondary;
        hCtx.globalAlpha = 0.42 + audio.mid * 0.25;
        hCtx.lineWidth = 1.75;
        hCtx.lineCap = 'round';
        for (let a = 0; a < 2; a++) {
          const start = a * Math.PI + 0.35;
          const end = start + Math.PI * 0.62;
          hCtx.beginPath();
          hCtx.arc(0, 0, baseR * (1.24 + audio.mid * 0.05), start, end);
          hCtx.stroke();
        }
        hCtx.restore();

        // 4. Pure concentric circular voice-reactive pulse rings (strictly round)
        const pulseR = baseR * (1.03 + audio.level * 0.1);
        hCtx.strokeStyle = cfg.primary;
        hCtx.globalAlpha = 0.72 + audio.level * 0.25;
        hCtx.lineWidth = 2.25;
        hCtx.beginPath();
        hCtx.arc(0, 0, pulseR, 0, Math.PI * 2);
        hCtx.stroke();

        // Secondary outer breathing circle
        hCtx.strokeStyle = cfg.secondary;
        hCtx.globalAlpha = 0.25 + audio.treble * 0.35;
        hCtx.lineWidth = 1.25;
        hCtx.beginPath();
        hCtx.arc(0, 0, baseR * (1.13 + audio.mid * 0.08), 0, Math.PI * 2);
        hCtx.stroke();

        // 5. Luminous glassy round core orb
        const coreR = baseR * (0.86 + audio.level * 0.06);
        const coreGrad = hCtx.createRadialGradient(-coreR * 0.28, -coreR * 0.28, coreR * 0.08, 0, 0, coreR);
        coreGrad.addColorStop(0, 'rgba(222, 248, 255, 0.32)');
        coreGrad.addColorStop(0.45, cfg.glow);
        coreGrad.addColorStop(0.85, 'rgba(6, 182, 212, 0.14)');
        coreGrad.addColorStop(1, 'rgba(14, 20, 22, 0.45)');
        hCtx.fillStyle = coreGrad;
        hCtx.globalAlpha = 1;
        hCtx.beginPath();
        hCtx.arc(0, 0, coreR, 0, Math.PI * 2);
        hCtx.fill();

        // Crisp circular rim highlight around core
        hCtx.strokeStyle = cfg.primary;
        hCtx.globalAlpha = 0.55 + audio.level * 0.35;
        hCtx.lineWidth = 1.75;
        hCtx.beginPath();
        hCtx.arc(0, 0, coreR, 0, Math.PI * 2);
        hCtx.stroke();

        // 6. True 3D Perspective-Projected Holographic Face Mesh inside the round orb
        const yaw = Math.sin(time * 0.55) * 0.28; // gentle 3D head turn
        const pitch = Math.cos(time * 0.4) * 0.08;
        const cosY = Math.cos(yaw), sinY = Math.sin(yaw);
        const cosP = Math.cos(pitch), sinP = Math.sin(pitch);
        const jawDrop = 0;
        const blink3D = (time % 4.5) > 4.35 ? 0.15 : 1.0;

        function project3D(x, y, z) {
          // Rotate Y (yaw) then X (pitch)
          const x1 = x * cosY - z * sinY;
          const z1 = z * cosY + x * sinY;
          const y2 = y * cosP - z1 * sinP;
          const z2 = z1 * cosP + y * sinP;
          const dist = 2.8;
          const p = dist / (dist - z2);
          return {
            sx: x1 * coreR * 0.86 * p,
            sy: y2 * coreR * 0.86 * p,
            z: z2,
            scale: p
          };
        }

        function draw3DCurve(pts, color, alpha, width, closed) {
          if (pts.length < 2) return;
          hCtx.strokeStyle = color;
          hCtx.globalAlpha = alpha;
          hCtx.lineWidth = width;
          hCtx.beginPath();
          pts.forEach((pt, idx) => {
            const pr = project3D(pt[0], pt[1], pt[2]);
            if (idx === 0) hCtx.moveTo(pr.sx, pr.sy);
            else hCtx.lineTo(pr.sx, pr.sy);
          });
          if (closed) hCtx.closePath();
          hCtx.stroke();
        }

        // 3D Cranium & Cheekbone Wireframe Ribbons (horizontal & vertical facial contours)
        const latLevels = [-0.62, -0.35, -0.08, 0.2, 0.48];
        latLevels.forEach((ly, idx) => {
          const rx = Math.sqrt(Math.max(0.05, 1 - ly * ly * 0.95)) * 0.72;
          const rz = rx * 0.92;
          const curve = [];
          for (let s = -10; s <= 10; s++) {
            const ang = (s / 10) * (Math.PI * 0.55);
            const x = Math.sin(ang) * rx;
            const z = Math.cos(ang) * rz;
            // Subtle nose/cheek sculpting on front face
            const sculptZ = z + (idx === 2 ? Math.exp(-x * x * 18) * 0.14 : 0);
            curve.push([x, ly, sculptZ]);
          }
          draw3DCurve(curve, cfg.secondary, 0.22 + audio.level * 0.15, 1.0, false);
        });

        // Vertical 3D Meridian Contours (nose bridge + cheek symmetry lines)
        const lonAngles = [-0.75, -0.42, 0, 0.42, 0.75];
        lonAngles.forEach((la) => {
          const curve = [];
          for (let s = -10; s <= 10; s++) {
            const phi = (s / 10) * 0.85;
            const y = Math.sin(phi) * 0.82;
            const r = Math.cos(phi) * 0.72;
            const x = Math.sin(la) * r;
            let z = Math.cos(la) * r * 0.92;
            // Sculpt 3D nose bridge along center meridian
            if (la === 0 && y > -0.28 && y < 0.22) {
              z += (0.22 - Math.abs(y + 0.02)) * 0.48;
            }
            // Sculpt chin & jaw drop
            const yAdj = y > 0.35 ? y + jawDrop * 0.35 : y;
            curve.push([x, yAdj, z]);
          }
          draw3DCurve(curve, la === 0 ? cfg.primary : cfg.secondary, la === 0 ? 0.45 : 0.22, la === 0 ? 1.3 : 1.0, false);
        });

        // 3D Jawline & Chin Contour (reacts to speech)
        const jawCurve = [
          [-0.62, 0.08, 0.15],
          [-0.52, 0.42 + jawDrop * 0.3, 0.32],
          [-0.28, 0.68 + jawDrop * 0.7, 0.52],
          [0, 0.76 + jawDrop, 0.62],
          [0.28, 0.68 + jawDrop * 0.7, 0.52],
          [0.52, 0.42 + jawDrop * 0.3, 0.32],
          [0.62, 0.08, 0.15]
        ];
        draw3DCurve(jawCurve, cfg.primary, 0.52 + audio.level * 0.25, 1.5, false);

        // 3D Brow Ridges & Glowing 3D Eye Sockets
        [-1, 1].forEach(side => {
          const brow = [
            [side * 0.12, -0.22, 0.64],
            [side * 0.26, -0.27, 0.62],
            [side * 0.44, -0.21, 0.48]
          ];
          draw3DCurve(brow, cfg.primary, 0.6, 1.6, false);

          // 3D Eye Diamond/Almond Contour
          const ey = -0.11;
          const eh = 0.065 * blink3D;
          const eyeRing = [
            [side * 0.16, ey, 0.63],
            [side * 0.28, ey - eh, 0.62],
            [side * 0.40, ey, 0.54],
            [side * 0.28, ey + eh, 0.60]
          ];
          draw3DCurve(eyeRing, cfg.primary, 0.85, 1.5, true);

          // Glowing 3D Optic Iris
          const iris = project3D(side * 0.28, ey, 0.62);
          hCtx.fillStyle = cfg.primary;
          hCtx.globalAlpha = currentMode === 'standby' ? 0.3 : 0.95;
          hCtx.beginPath();
          hCtx.arc(iris.sx, iris.sy, 3.2 * iris.scale * (coreR / 100), 0, Math.PI * 2);
          hCtx.fill();
        });

        // 3D Voice-Reactive Holographic Lips / Mouth
        const upperLip = [
          [-0.22, 0.36, 0.60],
          [-0.08, 0.33, 0.67],
          [0, 0.35, 0.68],
          [0.08, 0.33, 0.67],
          [0.22, 0.36, 0.60]
        ];
        const lowerLip = [
          [-0.22, 0.36, 0.60],
          [-0.09, 0.40 + jawDrop * 0.85, 0.65],
          [0, 0.41 + jawDrop, 0.66],
          [0.09, 0.40 + jawDrop * 0.85, 0.65],
          [0.22, 0.36, 0.60]
        ];
        draw3DCurve(upperLip, cfg.primary, 0.85, 1.6, false);
        draw3DCurve(lowerLip, cfg.primary, 0.85, 1.6, false);

        // Glowing 3D Mesh Vertices (holographic point cloud highlights)
        const keyNodes = [
          [0, -0.58, 0.52], [-0.45, -0.35, 0.45], [0.45, -0.35, 0.45],
          [0, -0.18, 0.68], [0, 0.12, 0.78], [-0.36, 0.14, 0.56], [0.36, 0.14, 0.56],
          [0, 0.76 + jawDrop, 0.62]
        ];
        keyNodes.forEach(pt => {
          const pr = project3D(pt[0], pt[1], pt[2]);
          hCtx.fillStyle = '#FFFFFF';
          hCtx.globalAlpha = 0.5 + audio.level * 0.45;
          hCtx.beginPath();
          hCtx.arc(pr.sx, pr.sy, 1.6 * pr.scale * (coreR / 100), 0, Math.PI * 2);
          hCtx.fill();
        });

        hCtx.restore();
      }

      const byId = id => document.getElementById(id);
      const settings = byId('settings');
      const api = () => window.pywebview.api;
      let frame = {level:0,bands:[],wave:[],busy:false,state:'READY'};
      let lastState = '';
      let lastAnswer = 'Type a prompt or start the microphone.';
      let preview = false;
      function render(data) {
        frame = data;
        for (const [role,text] of data.messages) {
          appendMessage(role, role==='error' ? 'Error: '+text : text);
          if (role!=='user') lastAnswer=text;
        }
        if (lastState!==data.state || data.busy) preview=false;
        const mode = data.state==='READY'?'standby':data.state==='SPEAKING'?'speaking':
          ['RECORDING','CHECKING MIC'].includes(data.state)?'listening':'thinking';
        if (!preview && (lastState!==data.state || currentMode!==mode)) setMode(mode);
        if (!preview) {
          sidebarStatusText.textContent = data.state==='READY'?'STANDBY':data.state;
          liveCaption.textContent = data.busy ? ({RECORDING:'Listening. Press Stop when you finish.',
            SPEAKING:lastAnswer,THINKING:'Preparing a response…'}[data.state] || data.state) : lastAnswer;
        }
        lastState=data.state;
        micBtnTitle.textContent=data.recording?'Stop':'Mic off';
        micIcon.textContent=data.recording?'mic':'mic_off';
        micToggleBtn.setAttribute('aria-pressed',String(data.recording));
        micToggleBtn.disabled=liveMicBtn.disabled=data.busy && !data.recording;
        liveMicBtn.lastElementChild.textContent=data.recording?"Stop recording":"Use Live Mic";
        clearChatBtn.disabled=pulseTestBtn.disabled=byId('check').disabled=data.busy;
        chatForm.querySelector('button').disabled=data.busy;
        byId('device').disabled=data.busy;
        byId('audioSyncBadge').nextElementSibling.textContent=data.rate?(data.rate/1000).toFixed(1)+' KHZ':'AUDIO IDLE';
        toneMetrics.textContent=data.level>0?'LEVEL: '+(20*Math.log10(data.level)).toFixed(0)+' dBFS':'LEVEL: —';
        micSourceLabel.textContent=data.state==='SPEAKING'?'VOICE OUTPUT':data.recording?'LIVE INPUT':'IDLE';
        hologramStateTelemetry.textContent=data.level>0?'RESONANCE: ACTIVE':'RESONANCE: IDLE';
      }
      function bindClick(element, handler) {
        element.addEventListener('click',async()=>{try {await handler();} catch(e){appendMessage('error',String(e));}});
      }
      bindClick(micToggleBtn,()=>api().microphone(false));
      bindClick(pulseTestBtn,()=>api().test_voice());
      bindClick(clearChatBtn,async()=>{if(await api().clear()){chatFeed.replaceChildren();updateTurnCount();lastAnswer='Type a prompt or start the microphone.';}});
      bindClick(liveMicBtn,()=>api().microphone(false));
      bindClick(byId('audioSettingsBtn'),async()=>{
        settings.showModal();
        const device=byId('device'), previous=device.value;
        const inputs=await api().inputs();
        device.replaceChildren(new Option('System default',''),...inputs.map(x=>new Option(x.name,x.id)));
        device.value=previous;
      });
      byId('device').onchange=e=>api().select_input(e.target.value);
      byId('speech').onchange=e=>api().speak_replies(e.target.checked);
      bindClick(byId('sound'),()=>api().sound_settings());
      bindClick(byId('check'),async()=>{settings.close();await api().microphone(true);});
      chatForm.onsubmit=async e=>{
        e.preventDefault();
        const text=chatInput.value.trim();
        if (text && await api().send(text)) chatInput.value='';
      };
      modeButtons.forEach(btn=>bindClick(btn,()=>{
        if(frame.busy) return;
        preview=true; setMode(btn.dataset.mode);
        sidebarStatusText.textContent='STANDBY';
        liveCaption.textContent=btn.dataset.mode==='standby'?lastAnswer:modeConfig[currentMode].label+' · hologram preview';
      }));
      function drawAudio() {
        const w=waveformCanvas.width,h=waveformCanvas.height, cfg=modeConfig[currentMode];
        wCtx.clearRect(0,0,w,h);
        const bands=frame.bands, step=w/Math.max(1,bands.length);
        wCtx.fillStyle=cfg.secondary; wCtx.globalAlpha=.36;
        bands.forEach((v,i)=>wCtx.fillRect(i*step,h-v*h*.8,step*.72,v*h*.8));
        wCtx.globalAlpha=1; wCtx.strokeStyle=cfg.primary; wCtx.lineWidth=2;
        wCtx.beginPath(); wCtx.moveTo(0,h/2);
        frame.wave.forEach((v,i)=>wCtx.lineTo(i*w/(frame.wave.length-1),h/2-Math.tanh(v*4)*h*.46));
        wCtx.lineTo(w,h/2); wCtx.stroke();
      }
      function animate() {
        time+=.025;
        const bands=frame.bands;
        const energy=(a,b)=>Math.max(0,...bands.slice(a,b));
        drawHologram({level:Math.min(1,Math.sqrt(frame.level)*2),bass:energy(0,12),mid:energy(12,24),treble:energy(24,36)});
        drawAudio();requestAnimationFrame(animate);
      }
      async function poll() {
        try {render(await api().snapshot());}
        catch(e){liveCaption.textContent='Desktop connection unavailable.';}
        setTimeout(poll,65);
      }
      appendMessage('bot','Ready when you are. Type a prompt or turn on the microphone.');
      setMode('standby');
      animate();
      if(window.pywebview?.api) poll();
      else window.addEventListener('pywebviewready',poll,{once:true});
    })();
