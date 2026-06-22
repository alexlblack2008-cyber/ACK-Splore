/* Beer Die Rankings - Frontend Logic */

var SUPABASE_URL = 'https://vezdmpzbwqsujvmrqklx.supabase.co';
var SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlemRtcHpid3FzdWp2bXJxa2x4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIxMzc4MDEsImV4cCI6MjA5NzcxMzgwMX0.2WiHAwmVcURcpLzozxeaPLa_-sEztKDu2Aeei-WmxOc';
var sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

var currentUser = null;
var currentProfile = null;
var currentGroupId = null;
var currentGroupData = null;
var groupMembers = [];

/* ── Helpers ── */
function $(id) { return document.getElementById(id); }
function showView(name) {
  document.querySelectorAll('.view').forEach(function(v) { v.classList.remove('active'); });
  $('view-' + name).classList.add('active');
  if (name === 'dashboard') loadDashboard();
  if (name === 'group') loadGroupDetail();
}
function msgEl(id, text, type) {
  var el = $(id);
  if (!el) return;
  el.innerHTML = text ? '<div class="msg ' + type + '">' + text + '</div>' : '';
}

/* ── Auth ── */
function showAuthTab(tab) {
  $('auth-login').style.display = tab === 'login' ? 'block' : 'none';
  $('auth-signup').style.display = tab === 'signup' ? 'block' : 'none';
  var btns = $('auth-tabs').querySelectorAll('button');
  btns[0].className = tab === 'login' ? 'active' : '';
  btns[1].className = tab === 'signup' ? 'active' : '';
  msgEl('auth-msg', '', '');
}

async function doLogin() {
  msgEl('auth-msg', '', '');
  var email = $('login-email').value.trim();
  var pass = $('login-password').value;
  if (!email || !pass) return msgEl('auth-msg', 'Fill in all fields', 'error');
  var res = await sb.auth.signInWithPassword({ email: email, password: pass });
  if (res.error) return msgEl('auth-msg', res.error.message, 'error');
  await initSession();
}

async function doSignup() {
  msgEl('auth-msg', '', '');
  var email = $('signup-email').value.trim();
  var pass = $('signup-password').value;
  var name = $('signup-name').value.trim();
  if (!email || !pass || !name) return msgEl('auth-msg', 'Fill in all fields', 'error');
  var res = await sb.auth.signUp({ email: email, password: pass });
  if (res.error) return msgEl('auth-msg', res.error.message, 'error');
  // Update display name in profiles
  if (res.data && res.data.user) {
    await sb.from('profiles').upsert({ id: res.data.user.id, display_name: name });
  }
  msgEl('auth-msg', 'Check your email to confirm, then log in.', 'success');
}

async function doLogout() {
  await sb.auth.signOut();
  currentUser = null;
  currentProfile = null;
  showView('auth');
}

async function initSession() {
  var sess = await sb.auth.getSession();
  if (!sess.data.session) { showView('auth'); return; }
  currentUser = sess.data.session.user;
  var p = await sb.from('profiles').select('*').eq('id', currentUser.id).single();
  currentProfile = p.data;
  $('user-name').textContent = currentProfile ? currentProfile.display_name : currentUser.email;
  $('user-name2').textContent = currentProfile ? currentProfile.display_name : '';
  showView('dashboard');
}

/* ── Dashboard ── */
async function loadDashboard() {
  if (!currentUser) return;
  // Load groups
  var gm = await sb.from('group_members').select('group_id').eq('user_id', currentUser.id);
  var groupIds = (gm.data || []).map(function(r) { return r.group_id; });
  var list = $('groups-list');
  if (groupIds.length === 0) {
    list.innerHTML = '<p style="color:#aaa;">No groups yet. Create or join one!</p>';
    $('week-games').textContent = '0';
    $('week-wins').textContent = '0';
    $('week-rating-dir').textContent = '-';
    return;
  }
  var groups = await sb.from('groups').select('*').in('id', groupIds);
  // For each group compute user rating
  var html = '';
  var allRatings = [];
  for (var i = 0; i < (groups.data || []).length; i++) {
    var g = groups.data[i];
    var rating = await getUserRatingInGroup(g.id, currentUser.id);
    allRatings.push(rating);
    html += '<div class="group-card" onclick="openGroup(\'' + g.id + '\')">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
    html += '<span style="font-weight:600;">' + escHtml(g.name) + '</span>';
    html += '<span class="badge">' + (rating !== null ? rating.toFixed(1) : 'N/A') + '</span>';
    html += '</div></div>';
  }
  list.innerHTML = html;

  // Weekly report & all time stats
  await loadWeeklyReport(groupIds);
  await loadAllTimeStats(groupIds);
}

async function loadWeeklyReport(groupIds) {
  var now = new Date();
  var day = now.getDay();
  var monday = new Date(now);
  monday.setDate(now.getDate() - ((day + 6) % 7));
  monday.setHours(0, 0, 0, 0);
  var mondayStr = monday.toISOString().split('T')[0];

  var gamesRes = await sb.from('games').select('id, winning_team_index, teams, date').in('group_id', groupIds).gte('date', mondayStr);
  var weekGames = gamesRes.data || [];

  // Find which games this user was in
  var gameIds = weekGames.map(function(g) { return g.id; });
  var userGames = 0;
  var userWins = 0;
  if (gameIds.length > 0) {
    var gpRes = await sb.from('game_players').select('game_id, team_index').in('game_id', gameIds).eq('user_id', currentUser.id);
    var myPlays = gpRes.data || [];
    userGames = myPlays.length;
    for (var i = 0; i < myPlays.length; i++) {
      var game = weekGames.find(function(g) { return g.id === myPlays[i].game_id; });
      if (game && game.winning_team_index === myPlays[i].team_index) userWins++;
    }
  }

  $('week-games').textContent = userGames;
  $('week-wins').textContent = userWins;
  $('week-rating-dir').textContent = userGames > 0 ? (userWins >= userGames / 2 ? '↑' : '↓') : '-';
  $('week-rating-dir').style.color = userGames > 0 ? (userWins >= userGames / 2 ? '#7dd3c0' : '#e74c3c') : '#aaa';
}

async function loadAllTimeStats(groupIds) {
  var gamesRes = await sb.from('games').select('id, winning_team_index').in('group_id', groupIds);
  var games = gamesRes.data || [];
  if (games.length === 0) {
    $('alltime-empty').style.display = 'block';
    return;
  }
  $('alltime-empty').style.display = 'none';
  var gameIds = games.map(function(g) { return g.id; });
  var gpRes = await sb.from('game_players').select('*').in('game_id', gameIds).eq('user_id', currentUser.id);
  var myPlays = gpRes.data || [];
  if (myPlays.length === 0) {
    $('alltime-empty').style.display = 'block';
    return;
  }

  var t = { games: 0, wins: 0, throws: 0, hits: 0, catches: 0, drops: 0, dinks: 0, sinks: 0, fifa: 0, dungeons: 0 };
  myPlays.forEach(function(gp) {
    t.games++;
    var game = games.find(function(g) { return g.id === gp.game_id; });
    if (game && game.winning_team_index === gp.team_index) t.wins++;
    t.throws += gp.throws || 0;
    t.hits += gp.hits || 0;
    t.catches += gp.catches || 0;
    t.drops += gp.drops || 0;
    t.dinks += gp.dinks || 0;
    t.sinks += gp.sinks || 0;
    t.fifa += gp.fifa_successes || 0;
    t.dungeons += gp.dungeons || 0;
  });

  $('at-games').textContent = t.games;
  $('at-wins').textContent = t.wins;
  $('at-winpct').textContent = t.games > 0 ? Math.round(t.wins / t.games * 100) + '%' : '0%';
  $('at-hits').textContent = t.hits;
  $('at-hitpct').textContent = t.throws > 0 ? Math.round(t.hits / t.throws * 100) + '%' : '0%';
  $('at-catches').textContent = t.catches;
  $('at-catchpct').textContent = (t.catches + t.drops) > 0 ? Math.round(t.catches / (t.catches + t.drops) * 100) + '%' : '0%';
  $('at-dinks').textContent = t.dinks;
  $('at-sinks').textContent = t.sinks;
  $('at-fifa').textContent = t.fifa;
  $('at-dungeons').textContent = t.dungeons;
  $('at-drops').textContent = t.drops;
}

/* ── Groups ── */
function showModal(type) {
  hideModals();
  $('modal-' + type).classList.remove('hidden');
}
function hideModals() {
  $('modal-create').classList.add('hidden');
  $('modal-join').classList.add('hidden');
  msgEl('create-msg', '', '');
  msgEl('join-msg', '', '');
}

async function doCreateGroup() {
  var name = $('create-name').value.trim();
  if (!name) return msgEl('create-msg', 'Enter a group name', 'error');
  var code = generateCode();
  var res = await sb.from('groups').insert({ name: name, invite_code: code, created_by: currentUser.id }).select().single();
  if (res.error) return msgEl('create-msg', res.error.message, 'error');
  await sb.from('group_members').insert({ group_id: res.data.id, user_id: currentUser.id });
  $('create-name').value = '';
  hideModals();
  loadDashboard();
}

async function doJoinGroup() {
  var code = $('join-code').value.trim().toUpperCase();
  if (!code) return msgEl('join-msg', 'Enter an invite code', 'error');
  var g = await sb.from('groups').select('id').eq('invite_code', code).single();
  if (g.error || !g.data) return msgEl('join-msg', 'Invalid invite code', 'error');
  var ins = await sb.from('group_members').insert({ group_id: g.data.id, user_id: currentUser.id });
  if (ins.error) {
    if (ins.error.message.indexOf('duplicate') !== -1 || ins.error.code === '23505')
      return msgEl('join-msg', 'Already in this group', 'error');
    return msgEl('join-msg', ins.error.message, 'error');
  }
  $('join-code').value = '';
  hideModals();
  loadDashboard();
}

function generateCode() {
  var chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  var code = '';
  for (var i = 0; i < 6; i++) code += chars[Math.floor(Math.random() * chars.length)];
  return code;
}

function openGroup(id) {
  currentGroupId = id;
  showView('group');
}

/* ── Group Detail ── */
function showGroupTab(tab) {
  ['leaderboard', 'log-game', 'members'].forEach(function(t) {
    $('tab-' + t).style.display = t === tab ? 'block' : 'none';
  });
  var btns = $('group-tabs').querySelectorAll('button');
  btns.forEach(function(b) { b.className = ''; });
  var idx = tab === 'leaderboard' ? 0 : tab === 'log-game' ? 1 : 2;
  btns[idx].className = 'active';
  if (tab === 'log-game') buildGameForm();
}

async function loadGroupDetail() {
  if (!currentGroupId) return;
  var g = await sb.from('groups').select('*').eq('id', currentGroupId).single();
  currentGroupData = g.data;
  $('group-name').textContent = g.data ? g.data.name : '';
  $('invite-code-display').textContent = g.data ? g.data.invite_code : '';

  // Load members
  var mRes = await sb.from('group_members').select('user_id').eq('group_id', currentGroupId);
  var uids = (mRes.data || []).map(function(r) { return r.user_id; });
  var pRes = await sb.from('profiles').select('id, display_name').in('id', uids);
  groupMembers = pRes.data || [];

  // Members list
  var ml = $('members-list');
  ml.innerHTML = groupMembers.map(function(m) {
    return '<div style="padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05);">' + escHtml(m.display_name || 'Unknown') + '</div>';
  }).join('');

  // Show delete button only if current user is the group creator
  var delSection = $('delete-group-section');
  if (delSection) {
    if (g.data && g.data.created_by === currentUser.id) {
      delSection.classList.remove('hidden');
    } else {
      delSection.classList.add('hidden');
    }
  }

  // Leaderboard
  await loadLeaderboard();
  // Reset to leaderboard tab
  showGroupTab('leaderboard');
}

/* ── Leaderboard / BDR ── */
var MIN_GAMES = 3;
var WARNING_WEIGHT = 0.5;
var WEIGHTS = {
  winPct: 0.25,
  offensePerGame: 0.2,
  hitPct: 0.1,
  catchPct: 0.1,
  fifaPerGame: 0.1,
  dungeonPct: -0.1,
  heightFoulsPerGame: -0.075,
  overTableFoulsPerGame: -0.075
};


async function loadLeaderboard() {
  // Get all games in this group
  var gRes = await sb.from('games').select('id, winning_team_index').eq('group_id', currentGroupId);
  var games = gRes.data || [];
  if (games.length === 0) {
    $('leaderboard-body').innerHTML = '';
    $('leaderboard-empty').style.display = 'block';
    return;
  }
  $('leaderboard-empty').style.display = 'none';
  var gameIds = games.map(function(g) { return g.id; });
  var gpRes = await sb.from('game_players').select('*').in('game_id', gameIds);
  var allGp = gpRes.data || [];

  // Build per-player aggregates
  var playerMap = {};
  allGp.forEach(function(gp) {
    if (!playerMap[gp.user_id]) {
      playerMap[gp.user_id] = { games: 0, wins: 0, throws: 0, hits: 0, dinks: 0, sinks: 0,
        catches: 0, drops: 0, fifa_successes: 0, fifa_points: 0, dungeons: 0,
        height_calls: 0, height_warnings: 0, over_table_calls: 0, over_table_warnings: 0 };
    }
    var p = playerMap[gp.user_id];
    p.games++;
    var game = games.find(function(g) { return g.id === gp.game_id; });
    if (game && game.winning_team_index === gp.team_index) p.wins++;
    p.throws += gp.throws || 0;
    p.hits += gp.hits || 0;
    p.dinks += gp.dinks || 0;
    p.sinks += gp.sinks || 0;
    p.catches += gp.catches || 0;
    p.drops += gp.drops || 0;
    p.fifa_successes += gp.fifa_successes || 0;
    p.fifa_points += gp.fifa_successes || 0;
    p.dungeons += gp.dungeons || 0;
    p.height_calls += gp.height_calls || 0;
    p.height_warnings += gp.height_warnings || 0;
    p.over_table_calls += gp.over_table_calls || 0;
    p.over_table_warnings += gp.over_table_warnings || 0;
  });

  // Compute metrics
  var players = [];
  Object.keys(playerMap).forEach(function(uid) {
    var p = playerMap[uid];
    var g = p.games;
    var winPct = g > 0 ? (p.wins / g) * 100 : 0;
    var hitPct = p.throws > 0 ? (p.hits / p.throws) * 100 : 0;
    var catchPct = (p.catches + p.drops) > 0 ? (p.catches / (p.catches + p.drops)) * 100 : 0;
    var offensePerGame = g > 0 ? (p.dinks + p.sinks) / g : 0;
    var fifaPerGame = g > 0 ? p.fifa_points / g : 0;
    var dungeonPct = g > 0 ? (p.dungeons / g) * 100 : 0;
    var heightFouls = p.height_calls + p.height_warnings * WARNING_WEIGHT;
    var heightFoulsPerGame = g > 0 ? heightFouls / g : 0;
    var overTableFouls = p.over_table_calls + p.over_table_warnings * WARNING_WEIGHT;
    var overTableFoulsPerGame = g > 0 ? overTableFouls / g : 0;

    players.push({
      uid: uid, games: g, wins: p.wins,
      winPct: winPct, hitPct: hitPct, catchPct: catchPct,
      offensePerGame: offensePerGame, fifaPerGame: fifaPerGame,
      dungeonPct: dungeonPct, heightFoulsPerGame: heightFoulsPerGame,
      overTableFoulsPerGame: overTableFoulsPerGame
    });
  });

  // Min-max normalize and compute BDR
  var metrics = ['winPct', 'offensePerGame', 'hitPct', 'catchPct', 'fifaPerGame', 'dungeonPct', 'heightFoulsPerGame', 'overTableFoulsPerGame'];
  var mins = {}, maxs = {};
  metrics.forEach(function(m) {
    mins[m] = Infinity; maxs[m] = -Infinity;
    players.forEach(function(p) {
      if (p[m] < mins[m]) mins[m] = p[m];
      if (p[m] > maxs[m]) maxs[m] = p[m];
    });
  });

  function norm(val, metric) {
    var range = maxs[metric] - mins[metric];
    if (range === 0) return 50;
    return ((val - mins[metric]) / range) * 100;
  }

  players.forEach(function(p) {
    if (p.games < MIN_GAMES) { p.rating = null; return; }
    var score = 0;
    metrics.forEach(function(m) {
      score += norm(p[m], m) * WEIGHTS[m];
    });
    // Rescale to 0-100
    var totalPosW = 0, totalNegW = 0;
    metrics.forEach(function(m) { if (WEIGHTS[m] > 0) totalPosW += WEIGHTS[m]; else totalNegW += WEIGHTS[m]; });
    var maxScore = totalPosW * 100 + totalNegW * 0;
    var minScore = totalPosW * 0 + totalNegW * 100;
    var range = maxScore - minScore;
    p.rating = range > 0 ? ((score - minScore) / range) * 100 : 50;
  });

  // Sort by rating desc (null at bottom)
  players.sort(function(a, b) {
    if (a.rating === null && b.rating === null) return 0;
    if (a.rating === null) return 1;
    if (b.rating === null) return -1;
    return b.rating - a.rating;
  });

  // Name lookup
  var profileMap = {};
  groupMembers.forEach(function(m) { profileMap[m.id] = m.display_name || 'Unknown'; });
  // Fetch any missing profiles
  var missing = players.filter(function(p) { return !profileMap[p.uid]; }).map(function(p) { return p.uid; });
  if (missing.length > 0) {
    var mp = await sb.from('profiles').select('id, display_name').in('id', missing);
    (mp.data || []).forEach(function(m) { profileMap[m.id] = m.display_name || 'Unknown'; });
  }

  var tbody = $('leaderboard-body');
  tbody.innerHTML = players.map(function(p, i) {
    return '<tr>' +
      '<td>' + (i + 1) + '</td>' +
      '<td>' + escHtml(profileMap[p.uid] || 'Unknown') + '</td>' +
      '<td>' + (p.rating !== null ? p.rating.toFixed(1) : '<span style="color:#aaa">< ' + MIN_GAMES + ' games</span>') + '</td>' +
      '<td>' + p.games + '</td>' +
      '<td>' + p.winPct.toFixed(0) + '%</td>' +
      '<td>' + p.hitPct.toFixed(0) + '%</td>' +
      '<td>' + p.catchPct.toFixed(0) + '%</td>' +
      '<td>' + p.offensePerGame.toFixed(2) + '</td>' +
      '<td>' + p.fifaPerGame.toFixed(2) + '</td>' +
      '<td>' + p.dungeonPct.toFixed(0) + '%</td>' +
      '<td>' + p.heightFoulsPerGame.toFixed(2) + '</td>' +
      '<td>' + p.overTableFoulsPerGame.toFixed(2) + '</td>' +
      '</tr>';
  }).join('');
}

async function getUserRatingInGroup(groupId, userId) {
  var gRes = await sb.from('games').select('id, winning_team_index').eq('group_id', groupId);
  var games = gRes.data || [];
  if (games.length === 0) return null;
  var gameIds = games.map(function(g) { return g.id; });
  var gpRes = await sb.from('game_players').select('*').in('game_id', gameIds).eq('user_id', userId);
  var myGp = gpRes.data || [];
  if (myGp.length < MIN_GAMES) return null;

  // Need all players for normalization
  var allGpRes = await sb.from('game_players').select('*').in('game_id', gameIds);
  var allGp = allGpRes.data || [];

  var playerMap = {};
  allGp.forEach(function(gp) {
    if (!playerMap[gp.user_id]) {
      playerMap[gp.user_id] = { games: 0, wins: 0, throws: 0, hits: 0, dinks: 0, sinks: 0,
        catches: 0, drops: 0, fifa_points: 0, dungeons: 0,
        height_calls: 0, height_warnings: 0, over_table_calls: 0, over_table_warnings: 0 };
    }
    var p = playerMap[gp.user_id];
    p.games++;
    var game = games.find(function(g) { return g.id === gp.game_id; });
    if (game && game.winning_team_index === gp.team_index) p.wins++;
    p.throws += gp.throws || 0;
    p.hits += gp.hits || 0;
    p.dinks += gp.dinks || 0;
    p.sinks += gp.sinks || 0;
    p.catches += gp.catches || 0;
    p.drops += gp.drops || 0;
    p.fifa_points += gp.fifa_successes || 0;
    p.dungeons += gp.dungeons || 0;
    p.height_calls += gp.height_calls || 0;
    p.height_warnings += gp.height_warnings || 0;
    p.over_table_calls += gp.over_table_calls || 0;
    p.over_table_warnings += gp.over_table_warnings || 0;
  });

  var metrics = ['winPct', 'offensePerGame', 'hitPct', 'catchPct', 'fifaPerGame', 'dungeonPct', 'heightFoulsPerGame', 'overTableFoulsPerGame'];
  var computed = {};
  Object.keys(playerMap).forEach(function(uid) {
    var p = playerMap[uid];
    var g = p.games;
    computed[uid] = {
      winPct: g > 0 ? (p.wins / g) * 100 : 0,
      hitPct: p.throws > 0 ? (p.hits / p.throws) * 100 : 0,
      catchPct: (p.catches + p.drops) > 0 ? (p.catches / (p.catches + p.drops)) * 100 : 0,
      offensePerGame: g > 0 ? (p.dinks + p.sinks) / g : 0,
      fifaPerGame: g > 0 ? p.fifa_points / g : 0,
      dungeonPct: g > 0 ? (p.dungeons / g) * 100 : 0,
      heightFoulsPerGame: g > 0 ? (p.height_calls + p.height_warnings * WARNING_WEIGHT) / g : 0,
      overTableFoulsPerGame: g > 0 ? (p.over_table_calls + p.over_table_warnings * WARNING_WEIGHT) / g : 0
    };
  });

  var allPlayers = Object.keys(computed).map(function(uid) { return computed[uid]; });
  var mins = {}, maxs = {};
  metrics.forEach(function(m) {
    mins[m] = Infinity; maxs[m] = -Infinity;
    allPlayers.forEach(function(p) {
      if (p[m] < mins[m]) mins[m] = p[m];
      if (p[m] > maxs[m]) maxs[m] = p[m];
    });
  });

  function norm(val, metric) {
    var range = maxs[metric] - mins[metric];
    if (range === 0) return 50;
    return ((val - mins[metric]) / range) * 100;
  }

  var me = computed[userId];
  if (!me) return null;
  var score = 0;
  metrics.forEach(function(m) { score += norm(me[m], m) * WEIGHTS[m]; });
  var totalPosW = 0, totalNegW = 0;
  metrics.forEach(function(m) { if (WEIGHTS[m] > 0) totalPosW += WEIGHTS[m]; else totalNegW += WEIGHTS[m]; });
  var maxScore = totalPosW * 100;
  var minScore = totalNegW * 100;
  var range = maxScore - minScore;
  return range > 0 ? ((score - minScore) / range) * 100 : 50;
}

/* ── Log Game ── */
function buildGameForm() {
  var numTeams = parseInt($('num-teams').value);
  var ppt = parseInt($('players-per-team').value);
  var wt = $('winning-team');
  wt.innerHTML = '';
  for (var t = 0; t < numTeams; t++) {
    var opt = document.createElement('option');
    opt.value = t;
    opt.textContent = 'Team ' + (t + 1);
    wt.appendChild(opt);
  }

  // Build score inputs for each team
  var scoreDiv = $('score-inputs');
  var sh = '';
  for (var s = 0; s < numTeams; s++) {
    sh += '<div style="flex:1;min-width:80px;">';
    sh += '<label style="font-size:0.8em;color:#aaa;">Team ' + (s + 1) + ' Score</label>';
    sh += '<input type="number" id="team-score-' + s + '" value="0" min="0" style="margin-bottom:0;">';
    sh += '</div>';
  }
  scoreDiv.innerHTML = sh;

  var container = $('teams-container');
  container.innerHTML = '';
  var statFields = [
    { key: 'throws', label: 'Throws' }, { key: 'hits', label: 'Hits' },
    { key: 'dinks', label: 'Dinks' }, { key: 'sinks', label: 'Sinks' },
    { key: 'catches', label: 'Catches' }, { key: 'drops', label: 'Drops' },
    { key: 'fifa_successes', label: 'FIFA Successes' },
    { key: 'dungeons', label: 'Dungeons' },
    { key: 'height_calls', label: 'Height Calls' }, { key: 'height_warnings', label: 'Height Warnings' },
    { key: 'over_table_calls', label: 'Over-Table Calls' }, { key: 'over_table_warnings', label: 'Over-Table Warnings' }
  ];

  for (var t = 0; t < numTeams; t++) {
    var section = document.createElement('div');
    section.className = 'team-section';
    var h = '<h3>Team ' + (t + 1) + '</h3>';
    for (var p = 0; p < ppt; p++) {
      h += '<div class="player-stats">';
      h += '<select id="player-' + t + '-' + p + '" style="margin-bottom:8px;">';
      h += '<option value="">-- Select Player --</option>';
      groupMembers.forEach(function(m) {
        h += '<option value="' + m.id + '">' + escHtml(m.display_name || 'Unknown') + '</option>';
      });
      h += '</select>';
      h += '<div class="stat-grid">';
      statFields.forEach(function(sf) {
        h += '<div class="stat-item"><label>' + sf.label + '</label>';
        h += '<input type="number" id="stat-' + t + '-' + p + '-' + sf.key + '" value="0" min="0"></div>';
      });
      h += '</div></div>';
    }
    section.innerHTML = h;
    container.appendChild(section);
  }
}

async function doLogGame() {
  msgEl('log-msg', '', '');
  var numTeams = parseInt($('num-teams').value);
  var ppt = parseInt($('players-per-team').value);
  var winIdx = parseInt($('winning-team').value);
  var playedTo = parseInt($('game-played-to').value) || 11;
  var scores = [];
  for (var s = 0; s < numTeams; s++) {
    var scoreEl = $('team-score-' + s);
    scores.push(scoreEl ? parseInt(scoreEl.value) || 0 : 0);
  }

  var teams = [];
  var playerEntries = [];
  var usedPlayers = {};

  for (var t = 0; t < numTeams; t++) {
    var teamPlayerIds = [];
    for (var p = 0; p < ppt; p++) {
      var sel = $('player-' + t + '-' + p);
      var uid = sel ? sel.value : '';
      if (!uid) return msgEl('log-msg', 'Select all players', 'error');
      if (usedPlayers[uid]) return msgEl('log-msg', 'Player selected twice', 'error');
      usedPlayers[uid] = true;
      teamPlayerIds.push(uid);

      var stats = {};
      ['throws','hits','dinks','sinks','catches','drops','fifa_successes','dungeons','height_calls','height_warnings','over_table_calls','over_table_warnings'].forEach(function(key) {
        var el = $('stat-' + t + '-' + p + '-' + key);
        stats[key] = el ? parseInt(el.value) || 0 : 0;
      });
      stats.team_index = t;
      stats.user_id = uid;
      playerEntries.push(stats);
    }
    teams.push(teamPlayerIds);
  }

  // Insert game
  var gRes = await sb.from('games').insert({
    group_id: currentGroupId,
    date: new Date().toISOString().split('T')[0],
    winning_team_index: winIdx,
    teams: teams,
    played_to: playedTo,
    scores: scores,
    created_by: currentUser.id
  }).select().single();

  if (gRes.error) return msgEl('log-msg', gRes.error.message, 'error');

  // Insert game_players
  var gpRows = playerEntries.map(function(pe) {
    var row = Object.assign({}, pe);
    row.game_id = gRes.data.id;
    return row;
  });

  var gpRes = await sb.from('game_players').insert(gpRows);
  if (gpRes.error) return msgEl('log-msg', gpRes.error.message, 'error');

  msgEl('log-msg', 'Game logged!', 'success');
  await loadLeaderboard();
}

/* ── Delete Group ── */
function confirmDeleteGroup() {
  if (!currentGroupData) return;
  if (confirm('Are you sure you want to delete "' + currentGroupData.name + '"? This will remove all games, stats, and members. This cannot be undone.')) {
    doDeleteGroup();
  }
}

async function doDeleteGroup() {
  if (!currentGroupId || !currentGroupData) return;
  if (currentGroupData.created_by !== currentUser.id) return alert('Only the group creator can delete this group.');

  // Delete in order: game_players → games → group_members → group
  var gamesRes = await sb.from('games').select('id').eq('group_id', currentGroupId);
  var gameIds = (gamesRes.data || []).map(function(g) { return g.id; });

  if (gameIds.length > 0) {
    await sb.from('game_players').delete().in('game_id', gameIds);
  }
  await sb.from('games').delete().eq('group_id', currentGroupId);
  await sb.from('group_members').delete().eq('group_id', currentGroupId);
  var del = await sb.from('groups').delete().eq('id', currentGroupId);

  if (del.error) return alert('Error deleting group: ' + del.error.message);

  currentGroupId = null;
  currentGroupData = null;
  showView('dashboard');
}

/* ── Utils ── */
function escHtml(s) {
  if (!s) return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function copyInviteCode() {
  var code = $('invite-code-display').textContent;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(code);
  } else {
    var ta = document.createElement('textarea');
    ta.value = code;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  }
}

/* ── PWA ── */
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}

/* ── Init ── */
initSession();
