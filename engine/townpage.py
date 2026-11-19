"""The town view's page as text: its styles, its markup and its JavaScript.

`CORE_JS` only works things out (change lists, a person's place in a block, routes
along the streets, the week's round). It touches nothing on the page, so the tests run
it under Node. `PAGE_JS` draws and listens. `TEMPLATE` is the page both go into.
townview.py fills the page from the record.
"""

CORE_JS = r"""
var TownCore = (function () {
  "use strict";
  var STREET = 0.16;        // half the width of a street, in blocks: a block is drawn inside it
  var WALK = 0.03;          // the share of the week's round a walker takes to cover one block
  var MOST_TRAVEL = 0.6;    // however far apart the stops are, at most this much of the round is travel

  // The value in force in `week`: the last entry at or before it. null before the first.
  function at(track, week) {
    var lo = 0, hi = track.length / 2 - 1, found = -1;
    while (lo <= hi) {
      var mid = (lo + hi) >> 1;
      if (track[mid * 2] <= week) { found = mid; lo = mid + 1; } else { hi = mid - 1; }
    }
    return found < 0 ? null : track[found * 2 + 1];
  }

  // A number from 0 up to 1 that is always the same for the same id and salt.
  function rnd(id, salt) {
    var x = Math.imul(id + 1, 0x9E3779B1) ^ Math.imul(salt + 1, 0x85EBCA6B);
    x ^= x >>> 15; x = Math.imul(x, 0x2C1B3C6D);
    x ^= x >>> 12; x = Math.imul(x, 0x297A2D39);
    x ^= x >>> 15;
    return (x >>> 0) / 4294967296;
  }

  // A person's own place inside the block whose corner is (bx, by). Drawn, not recorded.
  function inBlock(bx, by, id, salt) {
    var pad = STREET + 0.05, room = 1 - 2 * pad;
    return { x: bx + pad + room * rnd(id, salt), y: by + pad + room * rnd(id, salt + 101), bx: bx, by: by };
  }

  // The same place pulled toward the middle of its block, for a building smaller than the block.
  function shrink(p, by) {
    return { x: p.bx + 0.5 + (p.x - p.bx - 0.5) * by, y: p.by + 0.5 + (p.y - p.by - 0.5) * by,
             bx: p.bx, by: p.by, stay: p.stay };
  }

  // The way from one place to another. Streets run on the whole numbers. Out of the block to
  // the street beside it, along that street, along the street beside the other block, and in.
  // `lane` (-1 to 1) is which side of the street this person keeps to.
  function route(a, b, lane) {
    if (a.bx === b.bx && a.by === b.by) return [[a.x, a.y], [b.x, b.y]];
    var off = (lane || 0) * STREET * 0.7;
    var sy = (b.by < a.by ? a.by : a.by + 1) + off;
    var sx = (b.bx < a.bx ? b.bx + 1 : b.bx) + off;
    return [[a.x, a.y], [a.x, sy], [sx, sy], [sx, b.y], [b.x, b.y]];
  }

  function length(pts) {
    var total = 0;
    for (var i = 1; i < pts.length; i++) total += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    return total;
  }

  // The point a share `f` (0 to 1) of the way along a route.
  function along(pts, f) {
    var left = Math.min(1, Math.max(0, f)) * length(pts);
    for (var i = 1; i < pts.length; i++) {
      var dx = pts[i][0] - pts[i - 1][0], dy = pts[i][1] - pts[i - 1][1], step = Math.hypot(dx, dy);
      if (left <= step) {
        var part = step > 0 ? left / step : 0;
        return [pts[i - 1][0] + dx * part, pts[i - 1][1] + dy * part];
      }
      left -= step;
    }
    return pts[pts.length - 1].slice();
  }

  // The week's round. `stops` are places in order, each with a `stay` weight; the first and
  // last are home. `pace` is the share of the round one block takes. Returns the stops, the
  // route of each leg, and `t`: the moments the person leaves a stop or reaches the next,
  // from 0 to 1.
  function plan(stops, pace, lane) {
    var legs = [], times = [], travel = 0, weight = 0, i;
    for (i = 1; i < stops.length; i++) {
      var pts = route(stops[i - 1], stops[i], lane), time = length(pts) * pace;
      legs.push(pts); times.push(time); travel += time;
    }
    var squeeze = travel > MOST_TRAVEL ? MOST_TRAVEL / travel : 1;
    for (i = 0; i < stops.length; i++) weight += stops[i].stay || 0;
    var rest = 1 - travel * squeeze, t = [0], now = 0;
    for (i = 0; i < stops.length; i++) {
      now += weight > 0 ? rest * (stops[i].stay || 0) / weight : rest / stops.length;
      t.push(now);
      if (i < legs.length) { now += times[i] * squeeze; t.push(now); }
    }
    t[t.length - 1] = 1;
    return { stops: stops, legs: legs, t: t };
  }

  // Where the person is at `phase` (0 to 1) of the round, and whether they are on the road.
  function where(plan, phase) {
    var t = plan.t, last = plan.stops.length - 1, j = 0;
    if (!(phase > 0)) return { x: plan.stops[0].x, y: plan.stops[0].y, moving: false };
    if (phase >= 1) return { x: plan.stops[last].x, y: plan.stops[last].y, moving: false };
    while (j < t.length - 2 && phase >= t[j + 1]) j++;
    if (j % 2 === 0) return { x: plan.stops[j / 2].x, y: plan.stops[j / 2].y, moving: false };
    var span = t[j + 1] - t[j];
    var p = along(plan.legs[(j - 1) / 2], span > 0 ? (phase - t[j]) / span : 1);
    return { x: p[0], y: p[1], moving: true };
  }

  // --- numbers and dates in words ----------------------------------------------------------
  function pct(share) {
    var v = share * 100, tenths = Math.round(v * 10) / 10;
    return (tenths >= 10 || tenths === 0 ? v.toFixed(0) : tenths.toFixed(1)) + "%";
  }
  // The same, but a share still under `limit` is never rounded up to look as if it had reached it.
  function pctUnder(share, limit) {
    if (share < limit && pct(share) === pct(limit)) return (Math.floor(share * 1000 + 1e-9) / 10).toFixed(1) + "%";
    return pct(share);
  }
  // Week 0, when the founders arrive, is in year 1, quarter 1. Quarters end on weeks 13, 26 and so on.
  function whenText(week, year, quarter) {
    var inYear = Math.max(1, Math.round(year / quarter));
    return "Year " + Math.max(1, Math.ceil(week / year)) + ", quarter "
         + ((Math.max(1, Math.ceil(week / quarter)) - 1) % inYear + 1);
  }
  // Which recorded week to show for `week`: the last at or before it (the first, if none).
  function indexAt(weeks, week) {
    var lo = 0, hi = weeks.length - 1, found = 0;
    while (lo <= hi) {
      var mid = (lo + hi) >> 1;
      if (weeks[mid] <= week) { found = mid; lo = mid + 1; } else { hi = mid - 1; }
    }
    return found;
  }
  // The first recorded week at or after `week` (the last, if none): by then it has happened.
  function indexFrom(weeks, week) {
    for (var i = 0; i < weeks.length; i++) if (weeks[i] >= week) return i;
    return weeks.length - 1;
  }
  // A person's life lines have one point a quarter, from point `q0` of `qweeks`. Which of their
  // `count` points is the latest at or before `week`? -1 if none yet.
  function sampleAt(qweeks, q0, count, week) {
    var found = -1;
    for (var k = 0; k < count && qweeks[q0 + k] <= week; k++) found = k;
    return found;
  }
  // A list with one value for each recorded week, starting at recorded week number `first`:
  // its value for recorded week number `i`. null before the first, or past the end.
  function weekly(values, first, i) {
    var k = i - first;
    return k >= 0 && k < values.length ? values[k] : null;
  }

  // --- the week of one person --------------------------------------------------------------
  // The spot of every firm that exists and has premises in `week`.
  function firmSpots(firms, week) {
    var out = {};
    for (var i = 0; i < firms.length; i++) {
      var f = firms[i];
      if (f.end != null && week >= f.end) continue;
      var s = at(f.s, week);
      if (s != null && s >= 0) out[f.id] = s;
    }
    return out;
  }
  // A person's own place in the band under the map, where people with no home are drawn.
  function inStrip(id, W, H) {
    var pad = STREET + 0.05, x = pad + (W - 2 * pad) * rnd(id, 9);
    return { x: x, y: H + pad + (1 - 2 * pad) * rnd(id, 10), bx: Math.floor(x), by: H };
  }
  // What the record says about person `p` in `week`, and their round for it. null before they
  // arrive. `env` is the town that week: W, H, ride (how much faster a ride is), spots,
  // firmSpot (from firmSpots) and size(spot), how much of its block a building fills.
  function weekOf(p, week, env) {
    var home = at(p.h, week);
    if (home == null) return null;
    var q = { p: p, home: home, job: at(p.j, week), role: at(p.o, week), klass: at(p.k, week),
              mood: at(p.m, week), rides: at(p.r, week) === 1, food: at(p.f, week), fun: at(p.e, week), day: 0 };
    function placeOn(spot, salt) {
      var here = inBlock(env.spots[spot].x, env.spots[spot].y, p.id, salt), size = env.size(spot);
      return size < 1 ? shrink(here, size) : here;
    }
    function stop(place, weight) { return { x: place.x, y: place.y, bx: place.bx, by: place.by, stay: weight }; }
    var early = 0.3 + 0.4 * rnd(p.id, 3);           // how much of the time at home comes before setting out
    var base = home >= 0 ? placeOn(home, 1) : inStrip(p.id, env.W, env.H);
    var stops = [stop(base, 2 * early)];
    function visit(firm, salt, weight) {            // only a firm that has premises this week
      var spot = firm != null && firm >= 0 ? env.firmSpot[firm] : null;
      if (spot == null) return false;
      stops.push(stop(placeOn(spot, salt), weight));
      return true;
    }
    if (visit(q.job, 2, 4)) q.day = 1;              // where they spend the day: at work, else at home
    visit(q.food, 3, 1);
    visit(q.fun, 4, 1);
    stops.push(stop(base, 2 * (1 - early)));
    q.plan = plan(stops, WALK / (q.rides ? env.ride : 1), 2 * rnd(p.id, 5) - 1);
    return q;
  }

  // --- pointing ----------------------------------------------------------------------------
  // The person under the pointer: the nearest whose dot is within `reach` pixels. Each has x and y.
  function pickPerson(present, mx, my, reach) {
    var best = null, near = reach * reach;
    for (var i = 0; i < present.length; i++) {
      var dx = present[i].x - mx, dy = present[i].y - my, d = dx * dx + dy * dy;
      if (d < near) { near = d; best = present[i]; }
    }
    return best;
  }
  // What a point is over, in blocks: a spot (the block itself, or the street just above it where
  // its name is written), the strip for people with no home, or nothing.
  function blockAt(ux, uy, W, H) {
    var g = STREET, bx = Math.floor(ux), by = Math.floor(uy), fx = ux - bx, fy = uy - by;
    if (by === H && fy > g && fy < 1 - g) return ux > g && ux < W - g ? { type: "strip" } : null;
    if (bx < 0 || bx >= W || fx <= g || fx >= 1 - g) return null;
    if (by >= 0 && by < H && fy > g && fy < 1 - g) return { type: "spot", x: bx, y: by, name: false };
    var row = Math.round(uy);
    if (Math.abs(uy - row) > g) return null;
    if (row === H) return { type: "strip" };
    if (row >= 0 && row < H) return { type: "spot", x: bx, y: row + 0, name: true };
    return null;
  }

  // --- one person's life in words ----------------------------------------------------------
  // An event is [week, kind, firm, amount, word, word] and, when it stands for several in one
  // quarter, how many. `env` gives kinds, words, firm(id) for a firm's name and money(n).
  function lifeText(e, env) {
    var kind = env.kinds[e[1]], firm = env.firm(e[2]), amount = e[3], times = e[6] || 1;
    var a = e[4] >= 0 ? env.words[e[4]] : "", b = e[5] >= 0 ? env.words[e[5]] : "";
    var sum = env.money(amount), pay = sum + " a week";
    var again = times > 1 ? " (" + times + " times this quarter)" : "";
    function plain(word) { return String(word).replace(/_/g, " "); }
    function shares(n, sort) { return n.toLocaleString("en-AU") + " " + (sort || "") + (n === 1 ? "share" : "shares"); }
    switch (kind) {
      case "arrival":
        return (a === "founder" ? "Arrived to start a firm" : "Arrived for a job") + ", bringing " + sum;
      case "hire":
        return "Hired by " + firm + " at " + pay + (a === "moved" ? ", leaving another job" : "");
      case "layoff":
        return ({ laid_off: "Laid off by " + firm,
                  out_of_reach: "Lost the job at " + firm + ": could not get there",
                  wound_up: "Lost the job at " + firm + ": the firm was wound up",
                  firm_failed: "Lost the job at " + firm + ": the firm failed",
                  unpaid: "Lost the job at " + firm + ": it could not pay wages",
                  ousted: "Removed as chief executive of " + firm })[a]
               || "Lost the job at " + firm + " (" + plain(a) + ")";
      case "quit":
        return ({ moved: "Left " + firm + " for another job",
                  poached: "Left " + firm + " to run another firm",
                  founded: "Left " + firm + " to run their own firm" })[a] || "Left " + firm + " (" + plain(a) + ")";
      case "employer_changed": return "Their employer was taken over by " + firm + ", now paid " + pay;
      case "promotion": return "Promoted to executive at " + firm + ", " + pay;
      case "demotion": return "Moved back to staff at " + firm + ", " + pay;
      case "ceo_appointed": return "Made chief executive of " + firm + ", " + pay;
      case "firm_founded": return "Founded " + firm + " (" + a + ") with " + sum;
      case "founding_blocked": return "Could not start a " + a + " firm: " + plain(b);
      case "takeover": return "Bought " + firm + " for " + sum;
      case "control_change": return "Took control of " + firm;
      case "class_change":
        return a === "owner" ? "Joined the owner class" : a === "working" ? "Joined the working class" : "Now out of work";
      case "moved_home":
        return ({ cheaper: "Moved to a home that costs less once rent, fares and time on the road are counted",
                  reach: "Moved home to stay within reach of work", job: "Moved home for a job",
                  food: "Moved home to be within reach of food" })[a] || "Moved home";
      case "sub_start":
        if (a === "housing") return "Rented a home from " + firm + again;   // the rent depends on the block
        return (b === "switch" ? "Switched " + a + " to " + firm + ", " + pay
              : b === "needed" ? "Took " + a + " from " + firm + " because they needed it, " + pay
              : "Began paying " + firm + " for " + a + ", " + pay) + again;
      case "sub_end":
        return (({ budget: "Gave up " + a + ": could not afford it",
                   cut_off: "Cut off by " + firm + " after missed payments (" + a + ")",
                   evicted: "Evicted by " + firm + " after missed rent",
                   repossessed: firm + " took back the " + a + " after missed payments",
                   unserved: "Left " + firm + " (" + a + "): it could not serve them",
                   out_of_reach: "Lost " + a + ": " + firm + " was too far away",
                   redeveloped: "Put out of their home: it was pulled down for premises" })[b]
                || "Lost " + a + " (" + plain(b) + ")") + again;
      case "missed_payment":
        return times > 1 ? "Missed " + times + " payments to " + firm + " for " + a + " (" + sum + " in all)"
                         : "Missed a payment to " + firm + " for " + a + " (" + sum + ")";
      case "loan_missed":
        return times > 1 ? "Missed " + times + " loan payments (" + sum + " in all)" : "Missed a loan payment (" + sum + ")";
      case "loan_called":
        return times > 1 ? "The bank called in their loan " + times + " times, the largest " + sum
                         : "The bank called in their loan of " + sum;
      case "loan_repaid":
        return times > 1 ? "Finished repaying a called loan " + times + " times" : "Finished repaying the called loan";
      case "default": return "Defaulted: the bank wrote off " + sum;
      case "share_trade":
        if (b !== "sold") return "Bought " + shares(amount) + " in " + firm + (times > 1 ? " in " + times + " purchases" : "");
        var why = a === "distress" ? "to pay the bills" : a === "unhappy" ? "valuing them below the price"
                : a === "forced" ? "because the bank called in their loan" : "";
        var sold = "Sold " + shares(amount) + " in " + firm + (times > 1 ? " in " + times + " sales" : "");
        return why ? sold + (times > 1 || a === "unhappy" ? ", " : " ") + why : sold;
      case "share_issue":
        return "Bought " + shares(amount, "new ") + " in " + firm + (times > 1 ? " in " + times + " purchases" : "");
      case "cash_call":
        return "Put " + sum + " into " + firm + " to keep it going" + (times > 1 ? ", in " + times + " payments" : "");
      case "offer_refused": return "Turned down a job at " + firm + " paying " + pay;
      case "too_far":
        return (a === "job" ? "A job was too far to reach" : a.charAt(0).toUpperCase() + a.slice(1) + " was too far to reach") + again;
    }
    return plain(kind);
  }

  return { STREET: STREET, WALK: WALK, MOST_TRAVEL: MOST_TRAVEL, at: at, rnd: rnd, inBlock: inBlock,
           shrink: shrink, route: route, length: length, along: along, plan: plan, where: where,
           pct: pct, pctUnder: pctUnder, whenText: whenText, indexAt: indexAt, indexFrom: indexFrom,
           sampleAt: sampleAt, weekly: weekly, firmSpots: firmSpots, inStrip: inStrip, weekOf: weekOf,
           pickPerson: pickPerson, blockAt: blockAt, lifeText: lifeText };
})();
"""

PAGE_JS = r"""
(function () {
  "use strict";
  var DATA = JSON.parse(document.getElementById("data").textContent);
  var C = TownCore, NS = "http://www.w3.org/2000/svg";
  var W = DATA.map.w, H = DATA.map.h, weeks = DATA.weeks, N = weeks.length;
  var YEAR = DATA.run.year, QUARTER = DATA.run.quarter, STEP = DATA.run.step;
  var people = DATA.people, spots = DATA.spots, series = DATA.series;
  var SCOPES = ["all", "owner", "working", "out"];
  var KLASS = ["Owner class", "Working class", "Out of work"];
  var MOOD = ["Very unhappy", "Unhappy", "Content", "Well"];
  var ROLE = ["Works at ", "Staff at ", "An executive at ", "Chief executive of "];
  // A step is one recorded week. Most runs record every week; some record every fourth.
  var UNIT = STEP === 1 ? "week" : "recorded week";
  var AT_WORK = " People are shown where they spend the day: at work, or at home.";
  var SPEEDS = [
    { name: "Walk", wps: 0.125, round: true,
      note: "A " + UNIT + " takes eight seconds: slow enough to watch one person walk." },
    { name: "Slow", wps: 0.5, round: true,
      note: "A " + UNIT + " takes two seconds. People make their round: home, work, shops, home." },
    { name: "Fast", wps: 6, round: false, note: "Six " + UNIT + "s a second." + AT_WORK },
    { name: "Fastest", wps: 26, round: false,
      note: (STEP === 1 && YEAR === 52 ? "Half a year a second." : "Twenty-six " + UNIT + "s a second.") + AT_WORK }
  ];
  var EDGE = 0.2;                                   // blank margin round the map, in blocks

  var firms = {}, personAt = {}, spotAt = {}, MOST_STAFF = 1;
  DATA.firms.forEach(function (f) {
    firms[f.id] = f;
    for (var i = 1; i < f.n.length; i += 2) MOST_STAFF = Math.max(MOST_STAFF, f.n[i]);
  });
  people.forEach(function (p, i) { personAt[p.id] = i; });
  spots.forEach(function (s, i) { spotAt[s.x + "," + s.y] = i; });

  var $ = function (id) { return document.getElementById(id); };
  var canvas = $("town"), ctx = canvas.getContext("2d"), tip = $("tip");
  var t = 0.5;                 // whole part: which recorded week; the rest: how far through its round
  var playing = false, speed = 1, mode = "mood", sel = null, hot = null, pointer = null;
  var frame = -1, present = [], byPerson = {}, spotNow = [];
  var S = 40, cssW = 0, cssH = 0, col = {}, lastTick = 0, names = {};
  var lineX = null, lineY = null, cursor = null, cursorDot = null, lifeUI = null;

  // --- small helpers -----------------------------------------------------------------------
  function el(name, cls, parent, text) {
    var e = document.createElement(name);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }
  function svgEl(name, attrs, parent) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function money(dollars) {
    return (dollars < 0 ? "-$" : "$") + Math.abs(Math.round(dollars)).toLocaleString("en-AU");
  }
  function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }
  function count(n, one, many) { return n.toLocaleString("en-AU") + " " + (n === 1 ? one : many); }
  function yearOf(week) { return Math.max(1, Math.ceil(week / YEAR)); }
  function firmName(id) { return firms[id] ? firms[id].name : "a firm that has gone"; }
  var TELL = { kinds: DATA.kinds, words: DATA.words, firm: firmName, money: money };

  function readColours() {
    var cs = getComputedStyle(document.body);
    function v(name) { return cs.getPropertyValue(name).trim(); }
    col = {
      surface: v("--surface-1"), text: v("--text-primary"), text2: v("--text-secondary"),
      muted: v("--muted"), grid: v("--grid"), home: v("--home"), premises: v("--premises"),
      line: v("--block-line"),
      mood: [v("--mood-0"), v("--mood-1"), v("--mood-2"), v("--mood-3")],
      klass: [v("--series-1"), v("--series-2"), v("--series-3")]
    };
  }

  // --- the week ------------------------------------------------------------------------------
  // Everything the record says about one week, and each person's round for it.
  function prepare(i) {
    var week = weeks[i], firmSpot = C.firmSpots(DATA.firms, week);
    frame = i; present = []; byPerson = {};
    spotNow = spots.map(function (s) {
      var u = C.at(s.u, week);
      return { k: C.at(s.k, week) || 0, u: u == null ? -1 : u, n: C.at(s.n, week) || 0, lived: 0, size: 1 };
    });
    for (var id in firmSpot) {                      // a firm's building is sized by its staff
      var st = spotNow[firmSpot[id]];
      if (st.k === 2) st.size = 0.5 + 0.5 * Math.sqrt(Math.max(0, C.at(firms[id].n, week) || 0) / MOST_STAFF);
    }
    var env = { W: W, H: H, ride: DATA.run.ride, spots: spots, firmSpot: firmSpot,
                size: function (spot) { return spotNow[spot].k === 2 ? spotNow[spot].size : 1; } };
    people.forEach(function (p) {
      var q = C.weekOf(p, week, env);
      if (!q) return;                               // not in town yet
      q.x = 0; q.y = 0; q.moving = false;
      q.cash = C.weekly(p.c, p.c0, i); q.pay = C.at(p.w, week);     // their money that week, for their card
      if (q.home >= 0) spotNow[q.home].lived++;
      present.push(q);
      byPerson[p.id] = q;
    });
  }

  // Where everyone is at this moment of the round, in pixels.
  function locate(phase) {
    var round = SPEEDS[speed].round;
    for (var i = 0; i < present.length; i++) {
      var q = present[i], w;
      if (round) { w = C.where(q.plan, phase); }
      else { w = q.plan.stops[q.day]; w = { x: w.x, y: w.y, moving: false }; }
      q.x = (w.x + EDGE) * S; q.y = (w.y + EDGE) * S; q.moving = w.moving;
    }
  }

  // --- drawing -------------------------------------------------------------------------------
  function layout() {
    var room = $("mapwrap").clientWidth - 22;
    var tall = Math.max(280, window.innerHeight - 240);
    S = Math.max(14, Math.min(room / (W + 2 * EDGE), tall / (H + 1 + 2 * EDGE)));
    cssW = Math.round(S * (W + 2 * EDGE)); cssH = Math.round(S * (H + 1 + 2 * EDGE));
    var dpr = window.devicePixelRatio || 1;
    canvas.style.width = cssW + "px"; canvas.style.height = cssH + "px";
    canvas.width = Math.round(cssW * dpr); canvas.height = Math.round(cssH * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    names = {};
  }
  function box(x, y, w, h, r) {
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(x, y, w, h, r); else ctx.rect(x, y, w, h);
  }
  function corner(spot) {                           // the top left of a spot's block, in pixels
    return [(spots[spot].x + C.STREET + EDGE) * S, (spots[spot].y + C.STREET + EDGE) * S];
  }
  function strip() {                                // the band under the map for people with no home
    return [(C.STREET + EDGE) * S, (H + C.STREET + EDGE) * S, (W - 2 * C.STREET) * S, (1 - 2 * C.STREET) * S];
  }
  function drawBlocks() {
    var side = (1 - 2 * C.STREET) * S, r = Math.max(2, S * 0.07);
    ctx.lineWidth = 1;
    for (var i = 0; i < spots.length; i++) {
      var st = spotNow[i], c = corner(i), x = c[0], y = c[1];
      if (st.k === 1) {
        box(x, y, side, side, r); ctx.fillStyle = col.home; ctx.fill();
        ctx.strokeStyle = col.line; ctx.stroke();
      } else if (st.k === 2) {
        box(x, y, side, side, r); ctx.strokeStyle = col.grid; ctx.stroke();
        var b = side * st.size, o = (side - b) / 2;
        box(x + o, y + o, b, b, r); ctx.fillStyle = col.premises; ctx.fill();
        ctx.strokeStyle = col.line; ctx.stroke();
      } else if (st.k === 3) {
        box(x, y, side, side, r); ctx.fillStyle = col.surface; ctx.fill();
        ctx.lineWidth = 1.5; ctx.strokeStyle = col.muted; ctx.stroke(); ctx.lineWidth = 1;
      } else {
        box(x, y, side, side, r); ctx.strokeStyle = col.grid; ctx.stroke();
      }
    }
    var band = strip();
    ctx.setLineDash([4, 4]); box(band[0], band[1], band[2], band[3], r);
    ctx.strokeStyle = col.muted; ctx.stroke(); ctx.setLineDash([]);
  }
  function dotSize() { return Math.max(1.5, Math.min(3.4, S * 0.062)); }
  // Class is the shape (Jason, 16/11/2026): an owner a square, the working class a circle,
  // someone out of work a triangle, each about the same area and centred on the person.
  function personPath(q, r) {
    if (q.klass === 0) {
      var h = r * 0.89;
      ctx.rect(q.x - h, q.y - h, 2 * h, 2 * h);
    } else if (q.klass === 2) {
      var R = r * 1.5, w = R * 0.866;
      ctx.moveTo(q.x, q.y - R); ctx.lineTo(q.x + w, q.y + R / 2); ctx.lineTo(q.x - w, q.y + R / 2);
      ctx.closePath();
    } else {
      ctx.arc(q.x, q.y, r, 0, 6.2832);
    }
  }
  function drawPeople() {
    var r = dotSize(), last = null, palette = mode === "mood" ? col.mood : col.klass;
    ctx.lineWidth = 0.75; ctx.strokeStyle = col.surface;
    for (var i = 0; i < present.length; i++) {
      var q = present[i], c = palette[mode === "mood" ? q.mood : q.klass];
      if (c !== last) { ctx.fillStyle = c; last = c; }
      ctx.beginPath();
      personPath(q, r);
      ctx.fill();
      if (q.moving && q.rides) {                   // someone on the road by ride: a dark outline
        ctx.lineWidth = 1.25; ctx.strokeStyle = col.text; ctx.stroke();
        ctx.lineWidth = 0.75; ctx.strokeStyle = col.surface;
      } else {
        ctx.stroke();
      }
    }
  }
  function fit(text, most) {
    var key = text + "|" + Math.round(most);
    if (names[key]) return names[key];
    var out = text;
    if (ctx.measureText(out).width > most) {
      while (out.length > 2 && ctx.measureText(out + ".").width > most) out = out.slice(0, -1);
      out += ".";
    }
    names[key] = out;
    return out;
  }
  function spotName(i) {
    var st = spotNow[i];
    if (st.k === 2) return firms[st.u] ? cap(firms[st.u].need) : "";
    if (st.k === 3) return spots[i].label === "broker" ? "Broker" : cap(spots[i].label || "Service");
    return "";
  }
  function named(x, y) {                            // does the spot at (x, y) carry a name this week?
    var i = spotAt[x + "," + y];
    return i != null && spotName(i) !== "";
  }
  function drawNames() {
    var size = Math.max(8.5, Math.min(11, S * 0.2));
    ctx.font = "600 " + size + "px system-ui, -apple-system, 'Segoe UI', sans-serif";
    ctx.textBaseline = "middle"; ctx.lineJoin = "round"; ctx.lineWidth = 3;
    ctx.strokeStyle = col.surface; ctx.fillStyle = col.text2;
    if (S >= 30) {                                  // smaller than this the names cannot be read: the hover text has them
      ctx.textAlign = "center";
      for (var i = 0; i < spots.length; i++) {
        var name = spotName(i);
        if (!name) continue;
        var x = (spots[i].x + 0.5 + EDGE) * S, y = (spots[i].y + EDGE) * S;    // in the street above the block
        var free = !named(spots[i].x - 1, spots[i].y) && !named(spots[i].x + 1, spots[i].y);
        name = fit(name, S * (free ? 1.95 : 0.98));  // room to spread when the neighbours carry no name
        ctx.strokeText(name, x, y); ctx.fillText(name, x, y);
      }
    }
    var band = strip(), homeless = series.homeless[frame];
    var text = "No home" + (homeless != null ? ": " + homeless.toLocaleString("en-AU") : "");
    ctx.textAlign = "left";                         // the strip keeps its label at any size
    ctx.strokeText(text, band[0] + 2, band[1] - S * C.STREET);
    ctx.fillText(text, band[0] + 2, band[1] - S * C.STREET);
  }
  function outline(spot, width, colour) {
    var c = corner(spot), side = (1 - 2 * C.STREET) * S;
    box(c[0] - 2, c[1] - 2, side + 4, side + 4, Math.max(2, S * 0.07) + 2);
    ctx.lineWidth = width; ctx.strokeStyle = colour; ctx.stroke();
  }
  function ring(q, extra, width) {
    ctx.beginPath(); ctx.arc(q.x, q.y, dotSize() + extra, 0, 6.2832);
    ctx.lineWidth = width; ctx.strokeStyle = col.text; ctx.stroke();
  }
  function drawMarks() {
    if (hot && hot.type === "spot") outline(hot.id, 1.5, col.text2);
    if (sel && sel.type === "spot") outline(sel.id, 2, col.text);
    if (sel && sel.type === "strip" || hot && hot.type === "strip") {
      var band = strip();
      box(band[0] - 2, band[1] - 2, band[2] + 4, band[3] + 4, 5);
      ctx.lineWidth = 1.5; ctx.strokeStyle = col.text2; ctx.stroke();
    }
    var q = sel && sel.type === "person" ? byPerson[sel.id] : null;
    if (q) {                                        // the round of the person being followed
      ctx.globalAlpha = 0.55; ctx.lineWidth = 1.5; ctx.strokeStyle = col.text; ctx.lineJoin = "round";
      q.plan.legs.forEach(function (pts) {
        ctx.beginPath();
        pts.forEach(function (p, j) {
          if (j) ctx.lineTo((p[0] + EDGE) * S, (p[1] + EDGE) * S); else ctx.moveTo((p[0] + EDGE) * S, (p[1] + EDGE) * S);
        });
        ctx.stroke();
      });
      ctx.globalAlpha = 1;
      var palette = mode === "mood" ? col.mood : col.klass;
      ctx.beginPath(); personPath(q, dotSize() + 1.5);
      ctx.fillStyle = palette[mode === "mood" ? q.mood : q.klass]; ctx.fill();
      ring(q, 5, 2);
    }
    if (hot && hot.type === "person" && byPerson[hot.id] && !(sel && sel.type === "person" && sel.id === hot.id)) {
      ring(byPerson[hot.id], 3, 1.5);
    }
  }
  function draw() {
    ctx.clearRect(0, 0, cssW, cssH);
    drawBlocks(); drawPeople(); drawNames(); drawMarks();
  }
  function render() {
    var i = Math.min(N - 1, Math.max(0, Math.floor(t))), turned = i !== frame;
    if (turned) prepare(i);
    locate(t - i);
    if (turned) { updatePanel(); updateLine(); updateDetail(); pointAgain(); }
    draw();
  }

  // --- time ----------------------------------------------------------------------------------
  function seek(i) {
    i = Math.max(0, Math.min(N - 1, i));
    t = i + (SPEEDS[speed].round ? Math.min(0.999, t - Math.floor(t)) : 0.5);
    render();
  }
  function setPlaying(on) {
    if (on && Math.floor(t) >= N - 1) t = 0;        // on the last week: start again from the first
    playing = on;
    $("play").textContent = on ? "Pause" : "Play";
    $("play").setAttribute("aria-pressed", on ? "true" : "false");
    if (on) { lastTick = performance.now(); requestAnimationFrame(tick); }
  }
  function tick(now) {
    if (!playing) return;
    var dt = Math.min(0.1, (now - lastTick) / 1000);
    lastTick = now;
    t += dt * SPEEDS[speed].wps;
    if (t >= N - 0.001) { t = N - 0.001; setPlaying(false); }
    render();
    if (playing) requestAnimationFrame(tick);
  }
  function setSpeed(i) {
    speed = i;
    Array.prototype.forEach.call($("speeds").children, function (b, j) {
      b.setAttribute("aria-pressed", j === i ? "true" : "false");
    });
    $("speednote").textContent = SPEEDS[i].note
      + (STEP === 1 ? "" : " This run recorded people every " + STEP + "th week, so the page moves " + STEP + " weeks at a time.");
    render();
  }

  // --- the side panel ------------------------------------------------------------------------
  function updatePanel() {
    var i = frame, week = weeks[i];
    $("when").textContent = C.whenText(week, YEAR, QUARTER);
    $("whensub").textContent = "Week " + week + " of " + weeks[N - 1];
    SCOPES.forEach(function (scope) {
      var n = series.n[scope][i], u = series.unhappy[scope][i], nobody = !n || u == null;
      $("n-" + scope).textContent = n == null ? "" : n.toLocaleString("en-AU");
      $("u-" + scope).textContent = nobody ? "nobody" : scope === "all" ? C.pctUnder(u, DATA.run.fail) : C.pct(u);
      $("bar-" + scope).style.width = (nobody ? 0 : 100 * u) + "%";
    });
    function fact(id, value, text) { $(id).textContent = value == null ? "not recorded" : text(value); }
    function whole(v) { return v.toLocaleString("en-AU"); }
    function weekly(v) { return money(v / 100) + " a week"; }
    fact("f-homeless", series.homeless[i], whole);
    fact("f-destitute", series.destitute[i], whole);
    fact("f-riders", series.riders[i], C.pct);
    fact("f-jobless", series.jobless[i], C.pct);
    fact("f-wage", series.wage[i], weekly);
    fact("f-basket", series.basket[i], weekly);
    fact("f-firms", series.firms[i], whole);
    var slider = $("seek");
    slider.value = i;
    slider.setAttribute("aria-valuetext", C.whenText(week, YEAR, QUARTER) + ", week " + week);
  }
  function buildLegend() {
    var ul = $("legend");
    ul.textContent = "";
    var SHAPE = ["owner", "working", "out"];
    if (mode === "mood") {
      [3, 2, 1, 0].forEach(function (k) {
        var li = el("li", null, ul);
        el("span", "key-dot", li).style.background = "var(--mood-" + k + ")";
        el("span", null, li, MOOD[k]);
      });
    }
    [0, 1, 2].forEach(function (k) {                // the shape is the class, in either colouring
      var li = el("li", mode === "mood" ? "shape" : null, ul);
      var mark = el("span", "key-shape " + SHAPE[k], li);
      if (mode !== "mood") mark.style.background = "var(--series-" + (k + 1) + ")";
      el("span", null, li, KLASS[k]);
    });
    el("li", "note", ul, mode === "mood"
      ? "Unhappy means wellbeing under " + DATA.run.cutoff + ". The town fails when " + C.pct(DATA.run.fail) + " of everyone is unhappy. "
        + "The shape is the class."
      : "Class is by role, and is worked out again every week.");
    var li = el("li", "note", ul);
    el("span", "key-ride", li);
    el("span", null, li, "A dark outline is someone riding. In the model a ride is " + DATA.run.ride + " times as fast as walking.");
    Array.prototype.forEach.call(document.querySelectorAll("[data-mode]"), function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-mode") === mode ? "true" : "false");
    });
  }

  // --- the time line -------------------------------------------------------------------------
  // The share unhappy for every week the run measured, whatever weeks the people were recorded.
  function buildLine() {
    var host = $("line"), all = DATA.line;
    host.textContent = "";
    var w = Math.max(280, host.clientWidth), L = 40, R = 12, B = 22;
    var s = svgEl("svg", { width: w, role: "img",
                           "aria-label": "Share of everyone who is unhappy, week by week" }, host);
    var first = Math.min(weeks[0], all.weeks.length ? all.weeks[0] : weeks[0]);
    var last = Math.max(weeks[N - 1], all.weeks.length ? all.weeks[all.weeks.length - 1] : weeks[N - 1]);
    var span = Math.max(1, last - first);
    lineX = function (week) { return L + (w - L - R) * (week - first) / span; };
    // The key moments. Each name goes in the first row where it does not run into another.
    var rowEnd = [], placed = [];
    DATA.marks.forEach(function (m) {
      var label = svgEl("text", { "class": "label" }, s);
      label.textContent = m.label;
      var tw = label.getComputedTextLength ? label.getComputedTextLength() : m.label.length * 7;
      var x = lineX(m.week);
      var x0 = Math.max(2, x + 4 + tw > w - R ? x - 4 - tw : x + 4);   // near the right edge: left of its line
      var row = 0;
      while (rowEnd[row] != null && x0 < rowEnd[row] + 8) row++;
      rowEnd[row] = x0 + tw;
      label.setAttribute("x", x0);
      label.setAttribute("y", 11 + 14 * row);
      placed.push(x);
    });
    var T = 8 + 14 * Math.max(1, rowEnd.length), h = T + 70 + B;
    s.setAttribute("viewBox", "0 0 " + w + " " + h);
    s.setAttribute("height", h);
    lineY = function (v) { return T + (h - T - B) * (1 - v); };
    [0, 0.5, 1].forEach(function (v) {
      svgEl("line", { x1: L, x2: w - R, y1: lineY(v), y2: lineY(v), stroke: "var(--grid)", "stroke-width": 1 }, s);
      svgEl("text", { x: L - 6, y: lineY(v) + 4, "text-anchor": "end" }, s).textContent = (v * 100) + "%";
    });
    var step = 50;                                  // years between labels: far enough apart to read
    [20, 10, 5, 2, 1].forEach(function (years) { if ((w - L - R) * years * YEAR / span >= 60) step = years; });
    for (var y = step; y * YEAR <= last; y += step) {
      if (y * YEAR < first || lineX(y * YEAR) > w - R - 18) continue;
      svgEl("text", { x: lineX(y * YEAR), y: h - 6, "text-anchor": "middle" }, s).textContent = "Year " + y;
    }
    var fail = DATA.run.fail;
    svgEl("line", { x1: L, x2: w - R, y1: lineY(fail), y2: lineY(fail), stroke: "var(--text-secondary)",
                    "stroke-width": 1, "stroke-dasharray": "5 4" }, s);
    svgEl("text", { x: L + 4, y: lineY(fail) + 13, "class": "label" }, s).textContent =
      C.pct(fail) + ": the town fails";
    placed.forEach(function (x) {
      svgEl("line", { x1: x, x2: x, y1: T - 3, y2: h - B, stroke: "var(--axis)", "stroke-width": 1 }, s);
    });
    var d = "";
    all.unhappy.forEach(function (v, i) {
      d += (i ? "L" : "M") + lineX(all.weeks[i]).toFixed(1) + " " + lineY(v).toFixed(1);
    });
    svgEl("path", { d: d, fill: "none", stroke: "var(--ink-series)", "stroke-width": 2,
                    "stroke-linejoin": "round", "stroke-linecap": "round" }, s);
    cursor = svgEl("line", { y1: T - 3, y2: h - B, stroke: "var(--text-primary)", "stroke-width": 1.5 }, s);
    cursorDot = svgEl("circle", { r: 4, fill: "var(--text-primary)", stroke: "var(--surface-1)", "stroke-width": 2 }, s);
    var dragging = false;
    function toWeek(evt) {
      var rect = s.getBoundingClientRect(), x = (evt.clientX - rect.left) * w / rect.width;
      seek(C.indexAt(weeks, Math.round(first + span * Math.max(0, Math.min(1, (x - L) / (w - L - R))))));
    }
    s.addEventListener("pointerdown", function (evt) { dragging = true; s.setPointerCapture(evt.pointerId); toWeek(evt); });
    s.addEventListener("pointermove", function (evt) { if (dragging) toWeek(evt); });
    s.addEventListener("pointerup", function () { dragging = false; });
    s.addEventListener("pointercancel", function () { dragging = false; });
    $("seekwrap").style.padding = "0 " + (R - 8) + "px 0 " + (L - 8) + "px";
    updateLine();
  }
  function updateLine() {
    if (!cursor || frame < 0) return;
    var x = lineX(weeks[frame]), v = series.unhappy.all[frame];
    cursor.setAttribute("x1", x); cursor.setAttribute("x2", x);
    cursorDot.setAttribute("cx", x);
    cursorDot.setAttribute("cy", lineY(v == null ? 0 : v));
  }

  // --- pointing and picking ------------------------------------------------------------------
  // What is under a point of the window: a person only if the pointer is on their dot, else
  // the block, the name written above it, or the strip.
  function hit(at) {
    var rect = canvas.getBoundingClientRect(), mx = at.clientX - rect.left, my = at.clientY - rect.top;
    var q = C.pickPerson(present, mx, my, dotSize() + 3);
    if (q) return { type: "person", id: q.p.id };
    var over = C.blockAt(mx / S - EDGE, my / S - EDGE, W, H);
    if (!over) return null;
    if (over.type === "strip") return { type: "strip" };
    var spot = spotAt[over.x + "," + over.y];
    if (spot == null || (over.name && spotName(spot) === "")) return null;
    return { type: "spot", id: spot };
  }
  function nowParts(q) {
    return [
      KLASS[q.klass],
      q.job >= 0 ? (ROLE[q.role] || ROLE[0]) + firmName(q.job) : q.klass === 2 ? "" : "No job",
      q.home >= 0 ? (spotNow[q.home].u >= 0 ? "Rents from " + firmName(spotNow[q.home].u) : "Has a home") : "No home",
      MOOD[q.mood],
      q.rides ? "Pays for a ride" : "Walks"
    ].filter(function (part) { return part !== ""; });
  }
  // A person's card (Jason, 13/11/2026): the same, with their money that week under their class.
  function cardParts(q) {
    var parts = nowParts(q);
    return parts.slice(0, 1).concat(
      [q.cash != null ? "Cash " + money(q.cash) : "", q.pay > 0 ? "Pay " + money(q.pay) + " a week" : "No pay"],
      parts.slice(1));
  }
  function spotInfo(h) {
    if (h.type === "strip") {
      var n = series.homeless[frame];
      return ["No home", [(n == null ? "People" : count(n, "person has", "people have")) + " no home this week.",
                          "The model gives them no place on the map, so they are drawn here."]];
    }
    var st = spotNow[h.id], week = weeks[frame];
    if (st.k === 1) {
      return ["Homes", [st.u >= 0 ? "Landlord: " + firmName(st.u) : "Landlord not recorded this week",
                        count(st.n, "home", "homes") + ", " + st.lived + " lived in"]];
    }
    if (st.k === 2 && firms[st.u]) {
      var f = firms[st.u], price = C.at(f.p, week);
      return [f.name, [cap(f.need) + " firm, founded in year " + yearOf(f.founded),
                       (C.at(f.n, week) || 0) + " staff, " + count(C.at(f.c, week) || 0, "customer", "customers"),
                       price != null ? "Price " + money(price / 100) + " a week" : ""]];
    }
    if (st.k === 3) {
      return spots[h.id].label === "broker"
        ? ["Share broker", ["Where shares are bought and sold. It charges nothing."]]
        : ["Bank", ["Lends to firms and to people. It cannot fail."]];
    }
    return ["Empty land", ["Nothing stands here this week."]];
  }
  function showTip(at, title, lines) {
    tip.textContent = "";
    el("div", "when", tip, title);
    lines.forEach(function (text) { if (text) el("div", null, tip, text); });
    tip.style.display = "block";
    var w = tip.offsetWidth, h = tip.offsetHeight, x = at.clientX + 14, y = at.clientY + 14;
    if (x + w > window.innerWidth - 8) x = at.clientX - w - 14;
    if (y + h > window.innerHeight - 8) y = at.clientY - h - 14;
    tip.style.left = Math.max(8, x) + "px";
    tip.style.top = Math.max(8, y) + "px";
  }
  function showHot() {
    var q = hot && hot.type === "person" ? byPerson[hot.id] : null;
    if (!hot || !pointer || (hot.type === "person" && !q)) { tip.style.display = "none"; return; }
    if (q) {
      showTip(pointer, "Person " + hot.id, cardParts(q).concat(["Click to follow"]));
    } else {
      var info = spotInfo(hot);
      showTip(pointer, info[0], info[1]);
    }
  }
  // The week has changed under a pointer that has not moved: say what is under it now.
  function pointAgain() {
    if (!pointer) return;
    hot = hit(pointer);
    showHot();
  }
  function select(h) {
    sel = h;
    if (h && h.type === "person") $("who").value = h.id;
    renderDetail();
    draw();
  }

  // --- one person's life ---------------------------------------------------------------------
  // A small line of one number over the run, a point a quarter. The number beside it is the
  // latest point at or before the week shown, and a dot marks that point on the line.
  function spark(parent, label, values, q0, show, cutoff) {
    var row = el("div", "spark", parent);
    el("span", null, row, label);
    var holder = el("div", null, row), value = el("b", null, row);
    var w = 200, h = 34, first = weeks[0], span = Math.max(1, weeks[N - 1] - first);
    var s = svgEl("svg", { viewBox: "0 0 " + w + " " + h, preserveAspectRatio: "none", role: "img",
                           "aria-label": label + " over their time in town" }, holder);
    var top = cutoff != null ? 100 : Math.max.apply(null, values.concat([1]));
    function X(week) { return 1 + (w - 2) * (week - first) / span; }
    function Y(v) { return h - 3 - (h - 6) * v / top; }
    svgEl("line", { x1: 0, x2: w, y1: Y(0), y2: Y(0), stroke: "var(--grid)", "stroke-width": 1 }, s);
    if (cutoff != null) {
      svgEl("line", { x1: 0, x2: w, y1: Y(cutoff), y2: Y(cutoff), stroke: "var(--muted)", "stroke-width": 1,
                      "stroke-dasharray": "3 3", "vector-effect": "non-scaling-stroke" }, s);
    }
    var d = "";
    values.forEach(function (v, j) { d += (j ? "L" : "M") + X(DATA.qweeks[q0 + j]).toFixed(1) + " " + Y(v).toFixed(1); });
    svgEl("path", { d: d, fill: "none", stroke: "var(--ink-series)", "stroke-width": 1.5,
                    "stroke-linejoin": "round", "vector-effect": "non-scaling-stroke" }, s);
    var mark = svgEl("line", { y1: 0, y2: h, stroke: "var(--axis)", "stroke-width": 1,
                               "vector-effect": "non-scaling-stroke" }, s);
    var dot = svgEl("ellipse", { rx: 2.2, ry: 3, fill: "var(--text-primary)" }, s);
    return function (week) {
      mark.setAttribute("x1", X(week)); mark.setAttribute("x2", X(week));
      var j = C.sampleAt(DATA.qweeks, q0, values.length, week);
      value.textContent = j < 0 ? "" : show(values[j]);
      dot.setAttribute("visibility", j < 0 ? "hidden" : "visible");
      if (j >= 0) { dot.setAttribute("cx", X(DATA.qweeks[q0 + j])); dot.setAttribute("cy", Y(values[j])); }
    };
  }
  function renderDetail() {
    var host = $("detail");
    host.textContent = "";
    lifeUI = null;
    if (!sel) {
      el("p", "hint", host, "Click a person on the map, or pick one by number, to follow them. "
                           + "Point at a person to see their cash and pay that week. "
                           + "Point at a building, or at the name above a firm, to see whose it is.");
      return;
    }
    var head = el("div", "who", host);
    var title = el("span", null, head);
    el("button", null, head, "Clear").addEventListener("click", function () { select(null); });
    if (sel.type !== "person") {
      var info = spotInfo(sel);
      title.textContent = info[0];
      info[1].forEach(function (text) { if (text) el("p", "nowline", host, text); });
      return;
    }
    var p = people[personAt[sel.id]], life = p.life, came = life.events[0];
    title.textContent = "Person " + p.id;
    el("p", "nowline", host, came && DATA.kinds[came[1]] === "arrival"
       ? C.lifeText(came, TELL).replace("Arrived", "Arrived in year " + yearOf(p.arrived) + " (week " + p.arrived + ")") + "."
       : "Arrived in year " + yearOf(p.arrived) + " (week " + p.arrived + ").");
    var now = el("p", "nowline now", host);
    function ratio(v) { return (v / 100).toFixed(2); }
    var charts = [
      spark(host, "Cash", life.cash, life.q0, money),
      spark(host, "Weekly pay", life.pay, life.q0, money),
      spark(host, "Debt", life.loan, life.q0, money),
      spark(host, "Shares", life.shares, life.q0, money),
      spark(host, "Wellbeing", life.well, life.q0, ratio, DATA.run.cutoff * 100),
      spark(host, "Security", life.sec, life.q0, ratio, 100)
    ];
    var asat = el("p", "fine asat", host);
    el("p", "fine", host, "Each line runs from the start of the run to its end, with one point a quarter. "
                         + "The dashes on Wellbeing mark where unhappy begins.");
    el("div", "card-title", host, "What happened to them (" + life.events.length + ")");
    var list = el("ol", "life", host), rows = [];
    life.events.forEach(function (e) {
      var li = el("li", null, list), b = el("button", null, li);
      el("span", "date", b, "Year " + yearOf(e[0]) + ", week " + e[0]);
      el("span", null, b, C.lifeText(e, TELL));
      b.addEventListener("click", function () { seek(C.indexFrom(weeks, e[0])); });   // by then it has happened
      rows.push({ week: e[0], li: li });
    });
    lifeUI = { p: p, now: now, asat: asat, charts: charts, rows: rows, list: list, shown: -2 };
    updateDetail();
  }
  function updateDetail() {
    if (!lifeUI) {
      if (sel && sel.type !== "person") renderDetail();       // a place: say what it is this week
      return;
    }
    var week = weeks[frame], q = byPerson[lifeUI.p.id], life = lifeUI.p.life;
    lifeUI.now.textContent = q ? "Now: " + nowParts(q).join(". ") + "." : "Not in town yet in week " + week + ".";
    lifeUI.charts.forEach(function (update) { update(week); });
    var point = C.sampleAt(DATA.qweeks, life.q0, life.cash.length, week);
    lifeUI.asat.textContent = point >= 0
      ? "The number beside each line is its latest point, at week " + DATA.qweeks[life.q0 + point] + "."
      : life.cash.length ? "No point yet. The first is at week " + DATA.qweeks[life.q0] + "." : "";
    var k = -1;
    for (var i = 0; i < lifeUI.rows.length && lifeUI.rows[i].week <= week; i++) k = i;
    if (k === lifeUI.shown) return;
    lifeUI.rows.forEach(function (row, j) { row.li.className = j > k ? "later" : j === k ? "latest" : ""; });
    lifeUI.shown = k;
    if (k >= 0) {
      var li = lifeUI.rows[k].li, list = lifeUI.list;
      list.scrollTop = Math.max(0, li.offsetTop - list.clientHeight / 2);     // the list is the offset parent
    }
  }

  // --- wiring --------------------------------------------------------------------------------
  SPEEDS.forEach(function (sp, i) {
    var b = el("button", null, $("speeds"), sp.name);
    b.setAttribute("title", sp.note);
    b.addEventListener("click", function () { setSpeed(i); });
  });
  $("play").addEventListener("click", function () { setPlaying(!playing); });
  $("back").textContent = STEP === 1 ? "Back a week" : "Back " + STEP + " weeks";
  $("fwd").textContent = STEP === 1 ? "Forward a week" : "Forward " + STEP + " weeks";
  $("back").addEventListener("click", function () { seek(frame - 1); });
  $("fwd").addEventListener("click", function () { seek(frame + 1); });
  $("seek").max = N - 1;
  $("seek").addEventListener("input", function () { seek(+this.value); });
  Array.prototype.forEach.call(document.querySelectorAll("[data-mode]"), function (b) {
    b.addEventListener("click", function () { mode = b.getAttribute("data-mode"); buildLegend(); draw(); });
  });
  $("who").max = people.length ? people[people.length - 1].id : 1;
  function pick() {
    var id = parseInt($("who").value, 10);
    if (personAt[id] != null) { select({ type: "person", id: id }); return; }
    select(null);                                   // nobody is followed any more
    $("detail").textContent = "";
    el("p", "hint", $("detail"), "There is no person " + ($("who").value || "with that number")
       + ". People are numbered from " + people[0].id + " to " + people[people.length - 1].id + ".");
  }
  $("go").addEventListener("click", pick);
  $("who").addEventListener("keydown", function (evt) { if (evt.key === "Enter") pick(); });
  $("any").addEventListener("click", function () {
    if (present.length) select({ type: "person", id: present[Math.floor(Math.random() * present.length)].p.id });
  });
  canvas.addEventListener("pointermove", function (evt) {
    pointer = { clientX: evt.clientX, clientY: evt.clientY };
    hot = hit(pointer); showHot();
    if (!playing) draw();
  });
  canvas.addEventListener("pointerleave", function () {
    pointer = null; hot = null; tip.style.display = "none";
    if (!playing) draw();
  });
  canvas.addEventListener("click", function (evt) { select(hit(evt)); });
  // Space and the arrows work wherever the focus is, except while typing a person's number.
  document.addEventListener("keydown", function (evt) {
    var tag = (evt.target && evt.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || tag === "select") return;
    if (evt.key === " ") { evt.preventDefault(); setPlaying(!playing); }
    else if (evt.key === "ArrowRight") seek(frame + 1);
    else if (evt.key === "ArrowLeft") seek(frame - 1);
  });
  function resized() { layout(); buildLine(); locate(t - Math.floor(t)); draw(); }
  window.addEventListener("resize", resized);
  if (window.matchMedia) {
    var scheme = window.matchMedia("(prefers-color-scheme: dark)");
    if (scheme.addEventListener) scheme.addEventListener("change", function () { readColours(); draw(); });
  }

  readColours();
  layout();
  buildLegend();
  buildLine();
  setPlaying(false);
  setSpeed(speed);
  renderDetail();
})();
"""

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
.viz-root {
  color-scheme: light;
  --page: #f9f9f7; --surface-1: #fcfcfb; --text-primary: #0b0b0b; --text-secondary: #52514e;
  --muted: #898781; --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10);
  --wash: rgba(11,11,11,0.05); --ink-series: #52514e; --warning: #fab219;
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a;
  --home: #efeee9; --premises: #d6d5cc; --block-line: #cfcec4;
  --mood-0: #9e3432; --mood-1: #dd716a; --mood-2: #5598e7; --mood-3: #1c5cab;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) .viz-root {
    color-scheme: dark;
    --page: #0d0d0d; --surface-1: #1a1a19; --text-primary: #f0efec; --text-secondary: #c3c2b7;
    --muted: #898781; --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
    --wash: rgba(255,255,255,0.06); --ink-series: #c3c2b7; --warning: #fab219;
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
    --home: #262624; --premises: #3e3e3b; --block-line: #474743;
    --mood-0: #e4857e; --mood-1: #b13f3c; --mood-2: #256abf; --mood-3: #6da7ec;
  }
}
:root[data-theme="dark"] .viz-root {
  color-scheme: dark;
  --page: #0d0d0d; --surface-1: #1a1a19; --text-primary: #f0efec; --text-secondary: #c3c2b7;
  --muted: #898781; --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
  --wash: rgba(255,255,255,0.06); --ink-series: #c3c2b7; --warning: #fab219;
  --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
  --home: #262624; --premises: #3e3e3b; --block-line: #474743;
  --mood-0: #e4857e; --mood-1: #b13f3c; --mood-2: #256abf; --mood-3: #6da7ec;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--text-primary);
  font: 15px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1320px; margin: 0 auto; padding: 20px 16px 56px; }
h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
h2 { font-size: 17px; font-weight: 600; margin: 32px 0 12px; }
a { color: inherit; }
.sub { color: var(--text-secondary); font-size: 14px; }
.notice { display: flex; gap: 10px; align-items: flex-start; margin: 12px 0 0; padding: 8px 14px;
  background: var(--surface-1); border: 1px solid var(--border); border-left: 4px solid var(--warning);
  border-radius: 8px; font-size: 13.5px; color: var(--text-secondary); }
.notice strong { color: var(--text-primary); }
.icon { width: 16px; height: 16px; flex: none; margin-top: 2px; color: var(--text-primary); }
.stage { display: grid; grid-template-columns: minmax(0, 1fr) 356px; gap: 14px; align-items: start; margin-top: 16px; }
.mapcol { min-width: 0; }
.mapwrap { display: flex; justify-content: center; background: var(--surface-1); border: 1px solid var(--border);
  border-radius: 10px; padding: 10px; }
canvas { display: block; touch-action: manipulation; }
canvas:focus-visible { outline: 2px solid var(--series-1); outline-offset: 2px; }
.controls { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 12px 0 2px; }
.controls .label { font-size: 13px; color: var(--text-secondary); margin-left: 10px; }
#speeds { display: flex; flex-wrap: wrap; gap: 8px; }
.speednote { font-size: 13px; color: var(--text-secondary); min-height: 20px; margin: 4px 0 10px; }
button { font: inherit; font-size: 13px; color: var(--text-primary); background: var(--surface-1);
  border: 1px solid var(--border); border-radius: 999px; padding: 5px 12px; cursor: pointer; }
button:hover { background: var(--wash); }
button[aria-pressed="true"], button.primary { background: var(--text-primary); color: var(--surface-1);
  border-color: var(--text-primary); }
button.primary { min-width: 78px; font-weight: 600; }
button:focus-visible, input:focus-visible { outline: 2px solid var(--series-1); outline-offset: 2px; }
.card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 16px 12px; margin: 0; min-width: 0; }
.card-title { font-size: 15px; font-weight: 600; }
.card-note { font-size: 13px; color: var(--text-secondary); margin: 2px 0 6px; }
.plot svg { display: block; max-width: 100%; overflow: visible; cursor: pointer; touch-action: none; }
.plot text { font: 11.5px system-ui, -apple-system, "Segoe UI", sans-serif; fill: var(--muted);
  font-variant-numeric: tabular-nums; }
.plot text.label { fill: var(--text-secondary); font-size: 12px; paint-order: stroke; stroke: var(--surface-1);
  stroke-width: 4px; stroke-linejoin: round; }
input[type="range"] { display: block; width: 100%; margin: 4px 0 0; accent-color: var(--text-primary); }
.side { display: grid; gap: 14px; min-width: 0; }
.when { font-size: 26px; font-weight: 600; line-height: 1.15; }
.whensub { font-size: 13px; color: var(--text-secondary); margin-bottom: 10px; }
table.cover { border-collapse: collapse; width: 100%; font-size: 13.5px; }
table.cover th { text-align: right; font-weight: 400; font-size: 12px; color: var(--muted); padding: 0 0 4px 8px; }
table.cover th:first-child, table.cover td:first-child { text-align: left; padding-left: 0; }
table.cover td { padding: 4px 0 4px 8px; text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
table.cover td.pc { font-weight: 600; width: 58px; }
table.cover td.barcell { width: 34%; }
.bar { position: relative; height: 8px; background: var(--wash); border-radius: 4px; }
.bar i { position: absolute; left: 0; top: 0; bottom: 0; width: 0; background: var(--ink-series); border-radius: 4px; }
.bar b { position: absolute; top: -3px; bottom: -3px; width: 2px; margin-left: -1px; background: var(--text-primary); }
dl.facts { display: grid; grid-template-columns: 1fr auto; gap: 3px 12px; font-size: 13.5px; margin: 12px 0 0;
  padding-top: 10px; border-top: 1px solid var(--grid); }
dl.facts dt { color: var(--text-secondary); }
dl.facts dd { margin: 0; text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }
.filters { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 0 0 10px; }
.filters span { font-size: 13px; color: var(--text-secondary); margin-right: 4px; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 16px; font-size: 12.5px; color: var(--text-secondary);
  margin: 0; padding: 0; list-style: none; }
.legend li { display: flex; align-items: center; gap: 6px; }
.legend li.note { flex-basis: 100%; color: var(--muted); }
.key-dot { width: 10px; height: 10px; border-radius: 50%; flex: none; }
.key-shape { width: 10px; height: 10px; background: var(--muted); flex: none; }
.key-shape.owner { width: 9px; height: 9px; }
.key-shape.working { border-radius: 50%; }
.key-shape.out { width: 11px; height: 11px; clip-path: polygon(50% 0, 100% 100%, 0 100%); }
.key-ride { width: 10px; height: 10px; border-radius: 50%; flex: none; box-sizing: border-box;
  border: 1.5px solid var(--text-primary); background: var(--muted); }
.mapkey { margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--grid); }
.key-block { width: 12px; height: 12px; border-radius: 3px; flex: none; border: 1px solid var(--block-line); }
.key-home { background: var(--home); }
.key-firm { background: var(--premises); }
.key-service { background: var(--surface-1); border: 1.5px solid var(--muted); }
.key-empty { border-color: var(--grid); }
.key-strip { border: 1px dashed var(--muted); }
.pickrow { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; font-size: 13px; margin-top: 8px;
  color: var(--text-secondary); }
.pickrow input { width: 78px; font: inherit; font-size: 13px; padding: 4px 8px; border: 1px solid var(--border);
  border-radius: 8px; background: var(--surface-1); color: var(--text-primary); }
#detail { margin-top: 10px; font-size: 13.5px; }
#detail .hint, #detail .fine { color: var(--muted); font-size: 12.5px; margin: 6px 0; }
.who { display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; }
.nowline { color: var(--text-secondary); margin: 4px 0; }
.nowline.now { color: var(--text-primary); margin-bottom: 10px; }
.spark { display: grid; grid-template-columns: 11ch minmax(0, 1fr) 9ch; gap: 6px; align-items: center;
  font-size: 12.5px; color: var(--text-secondary); }
.spark svg { display: block; width: 100%; height: 34px; overflow: visible; }
.spark b { text-align: right; color: var(--text-primary); font-variant-numeric: tabular-nums; }
#detail .card-title { margin-top: 12px; }
ol.life { list-style: none; margin: 6px 0 0; padding: 0; max-height: 320px; overflow: auto;
  border-top: 1px solid var(--grid); position: relative; }
ol.life button { display: grid; grid-template-columns: 18ch minmax(0, 1fr); gap: 8px; width: 100%; text-align: left;
  border: 0; border-bottom: 1px solid var(--grid); border-radius: 0; background: none; padding: 5px 4px;
  font-size: 12.5px; }
ol.life button:hover { background: var(--wash); }
ol.life .date { color: var(--text-secondary); font-variant-numeric: tabular-nums; }
ol.life li.later button, ol.life li.later .date { color: var(--muted); }
ol.life li.latest button { background: var(--wash); font-weight: 600; }
#tip { position: fixed; z-index: 10; pointer-events: none; display: none; min-width: 150px; max-width: 320px;
  background: var(--surface-1); color: var(--text-primary); border: 1px solid var(--border);
  border-radius: 8px; padding: 8px 10px; font-size: 12.5px; box-shadow: 0 6px 24px rgba(0,0,0,0.14); }
#tip .when { font-size: 13px; font-weight: 600; line-height: 1.3; margin-bottom: 4px; }
footer p { font-size: 14px; color: var(--text-secondary); max-width: 82ch; margin: 6px 0; }
footer strong { color: var(--text-primary); }
footer .fine { font-size: 12.5px; color: var(--muted); }
@media (max-width: 940px) { .stage { grid-template-columns: minmax(0, 1fr); } }
</style>
</head>
<body class="viz-root">
<main>
__HEADER__
<div class="stage">
  <div class="mapcol">
    <div class="mapwrap" id="mapwrap">
      <canvas id="town" tabindex="0" role="img"
        aria-label="The town on its map. Every person is a dot. The numbers for the week shown are in the panel beside it."></canvas>
    </div>
    <div class="controls" role="group" aria-label="Replay">
      <button id="play" class="primary" aria-pressed="false">Play</button>
      <button id="back">Back</button>
      <button id="fwd">Forward</button>
      <span class="label">Speed</span>
      <span id="speeds" role="group" aria-label="Speed"></span>
    </div>
    <div class="speednote" id="speednote"></div>
    <figure class="card">
      <div class="card-title">Share of everyone who is unhappy</div>
      <div class="card-note">Click or drag on the chart, or use the slider, to go to any week.</div>
      <div class="plot" id="line"></div>
      <div id="seekwrap"><input type="range" id="seek" min="0" max="0" step="1" value="0" aria-label="Week shown"></div>
    </figure>
  </div>
  <aside class="side" aria-label="The week shown">
    <div class="card">
      <div class="when" id="when" aria-live="off"></div>
      <div class="whensub" id="whensub"></div>
      <table class="cover">
        <thead><tr><th scope="col">Who</th><th scope="col">People</th><th scope="col" colspan="2">Unhappy</th></tr></thead>
        <tbody>
          <tr><td>Everyone</td><td id="n-all"></td>
            <td class="barcell"><div class="bar"><i id="bar-all"></i><b style="left:__FAIL__%" title="The town fails here"></b></div></td>
            <td class="pc" id="u-all"></td></tr>
          <tr><td>Owner class</td><td id="n-owner"></td>
            <td class="barcell"><div class="bar"><i id="bar-owner"></i></div></td><td class="pc" id="u-owner"></td></tr>
          <tr><td>Working class</td><td id="n-working"></td>
            <td class="barcell"><div class="bar"><i id="bar-working"></i></div></td><td class="pc" id="u-working"></td></tr>
          <tr><td>Out of work</td><td id="n-out"></td>
            <td class="barcell"><div class="bar"><i id="bar-out"></i></div></td><td class="pc" id="u-out"></td></tr>
        </tbody>
      </table>
      <dl class="facts">
        <dt>People with no home</dt><dd id="f-homeless"></dd>
        <dt>Destitute</dt><dd id="f-destitute"></dd>
        <dt>Paying for a ride</dt><dd id="f-riders"></dd>
        <dt>Jobless rate</dt><dd id="f-jobless"></dd>
        <dt>Staff wage</dt><dd id="f-wage"></dd>
        <dt>Weekly basket</dt><dd id="f-basket"></dd>
        <dt>Firms</dt><dd id="f-firms"></dd>
      </dl>
    </div>
    <div class="card">
      <div class="filters" role="group" aria-label="Colour people by"><span>Colour people by</span>
        <button data-mode="mood" aria-pressed="true">Wellbeing</button>
        <button data-mode="klass" aria-pressed="false">Class</button></div>
      <ul class="legend" id="legend"></ul>
      <ul class="legend mapkey" aria-label="On the map">
        <li><span class="key-block key-home"></span>Homes</li>
        <li><span class="key-block key-firm"></span>A firm, bigger with more staff</li>
        <li><span class="key-block key-service"></span>Bank, broker</li>
        <li><span class="key-block key-empty"></span>Empty land</li>
        <li><span class="key-block key-strip"></span>People with no home</li>
      </ul>
    </div>
    <div class="card">
      <div class="card-title">Follow one person</div>
      <div class="pickrow"><label for="who">Person number</label>
        <input id="who" type="number" min="1" step="1" inputmode="numeric">
        <button id="go">Show</button><button id="any">Someone at random</button></div>
      <div id="detail"></div>
    </div>
  </aside>
</div>
__FOOTER__
</main>
<div id="tip" role="status" aria-live="polite"></div>
<script id="data" type="application/json">__DATA__</script>
<script>__CORE__</script>
<script>__PAGE__</script>
</body>
</html>
"""
