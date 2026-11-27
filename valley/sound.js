/* The valley's sound: every cue is synthesized in the browser (no audio files) and fired by something the scene
   is doing that frame. Pages call the cues; this file only knows how to make them.

   HLSound.toggle()            the Sound button: turns sound on or off and remembers the choice in this browser
   HLSound.isOn(), running()   the choice, and whether audio is actually playing (browsers wait for a tap or key)
   HLSound.wind(cameraY)       per frame: the wind's tone follows camera height (thin up high, warm in the meadow)
   HLSound.week(u)             a wooden tock when the week counter moves forward; u = week / weeks raises it over the year
   HLSound.flock(level)        one sheep bell, somewhere in the flock; level < 1 for ghosts
   HLSound.hero(pan)           the followed life's own bell, panned -1..1 to where she stands on screen
   HLSound.jobEnds()           a dull low bell (her job ends)
   HLSound.accelerator()       a bright chord (she leaves the flock's path)
   HLSound.converge()          the flock's bells strum into one chord (most lives end in the same corner)
   HLSound.dice(outcome)       the referee's dice: a rattle, then a tone for 'win', 'lose' or 'none' (life pages)

   Browsers only start audio after a tap, click or key press, and a scroll doesn't count. So sound is off until the
   reader presses the Sound button, and if they turned it on before, it wakes on their first tap or key press. */
(function(){
var ctx=null,master,bus,verb,noise,windSrc,windF,windG,on=false,want=false;
try{want=localStorage.getItem('hl-sound')==='on';}catch(e){}
on=want;

function init(){
  if(ctx)return true;
  var AC=window.AudioContext||window.webkitAudioContext;if(!AC)return false;
  ctx=new AC();
  var comp=ctx.createDynamicsCompressor();comp.threshold.value=-18;comp.ratio.value=4;
  master=ctx.createGain();master.gain.value=0;comp.connect(master);master.connect(ctx.destination);
  bus=ctx.createGain();bus.connect(comp);
  // a short open-air reverb: decaying noise, so the bells sound like they're outside
  var len=Math.floor(ctx.sampleRate*2.2),ir=ctx.createBuffer(2,len,ctx.sampleRate);
  for(var c=0;c<2;c++){var d=ir.getChannelData(c);for(var i=0;i<len;i++)d[i]=(Math.random()*2-1)*Math.pow(1-i/len,4);}
  verb=ctx.createConvolver();verb.buffer=ir;var vg=ctx.createGain();vg.gain.value=.28;bus.connect(verb);verb.connect(vg);vg.connect(comp);
  noise=ctx.createBuffer(1,ctx.sampleRate*2,ctx.sampleRate);var nd=noise.getChannelData(0);for(i=0;i<nd.length;i++)nd[i]=Math.random()*2-1;
  // the wind: looping noise through a moving band-pass, never through the reverb
  windSrc=ctx.createBufferSource();windSrc.buffer=noise;windSrc.loop=true;
  windF=ctx.createBiquadFilter();windF.type='bandpass';windF.Q.value=.6;windF.frequency.value=700;
  windG=ctx.createGain();windG.gain.value=.05;
  var lfo=ctx.createOscillator(),lg=ctx.createGain();lfo.frequency.value=.13;lg.gain.value=.025;lfo.connect(lg);lg.connect(windG.gain);lfo.start();
  windSrc.connect(windF);windF.connect(windG);windG.connect(comp);windSrc.start();
  return true;
}
function wake(){if(!on)return;if(!init())return;if(ctx.state!=='running')ctx.resume().catch(function(){});
  master.gain.cancelScheduledValues(ctx.currentTime);master.gain.setTargetAtTime(.9,ctx.currentTime,.3);}
function sleep(){if(!ctx)return;master.gain.cancelScheduledValues(ctx.currentTime);master.gain.setTargetAtTime(0,ctx.currentTime,.08);}
['pointerup','keydown','touchend'].forEach(function(ev){addEventListener(ev,function(){if(on&&(!ctx||ctx.state!=='running'))wake();},{capture:true,passive:true});});

function out(node,pan){if(pan&&ctx.createStereoPanner){var p=ctx.createStereoPanner();p.pan.value=pan;node.connect(p);p.connect(bus);}else node.connect(bus);}
function tone(t,f,dur,o){o=o||{};var osc=ctx.createOscillator(),G=ctx.createGain();osc.type=o.type||'sine';osc.frequency.setValueAtTime(f,t);
  if(o.to)osc.frequency.exponentialRampToValueAtTime(o.to,t+dur);
  var a=o.a||.004;G.gain.setValueAtTime(0,t);G.gain.linearRampToValueAtTime(o.g||.08,t+a);G.gain.exponentialRampToValueAtTime(1e-4,t+a+dur);
  osc.connect(G);out(G,o.pan||0);osc.start(t);osc.stop(t+a+dur+.05);}
function click(t,f,g,pan){var s=ctx.createBufferSource();s.buffer=noise;var fl=ctx.createBiquadFilter();fl.type='bandpass';fl.frequency.value=f;fl.Q.value=4;
  var G=ctx.createGain();G.gain.setValueAtTime(g,t);G.gain.exponentialRampToValueAtTime(1e-4,t+.03);s.connect(fl);fl.connect(G);out(G,pan||0);s.start(t,Math.random());s.stop(t+.05);}
// a sheep bell: thin metal, so the partials aren't harmonic
function bell(t,f,g,pan,len){[1,2.41,3.93,5.6].forEach(function(m,i){tone(t,f*m,(len||.9)/(i*.7+1),{g:g/(i*1.3+1),a:.002,pan:pan});});}
var SCALE=[392,440,523.25,587.33,659.25];   // the flock rings in one key, so many bells still sound like one field
function live(){return on&&ctx&&ctx.state==='running';}
var lastTock=0;

window.HLSound={
  isOn:function(){return on;},
  running:function(){return live();},
  toggle:function(){if(on&&!live()){wake();return;}on=!on;try{localStorage.setItem('hl-sound',on?'on':'off');}catch(e){}if(on)wake();else sleep();},
  wind:function(y){if(!live())return;var u=Math.max(0,Math.min(1,(y-20)/450));
    windF.frequency.setTargetAtTime(380+u*1900,ctx.currentTime,.4);windG.gain.setTargetAtTime(.035+u*.05,ctx.currentTime,.6);},
  week:function(u){if(!live())return;var t=ctx.currentTime;if(t-lastTock<.07)return;lastTock=t;
    var f=520*Math.pow(2,u*.9);tone(t,f,.07,{type:'triangle',g:.05,a:.002});click(t,f*3,.04);},
  flock:function(level){if(!live())return;var t=ctx.currentTime+Math.random()*.05,f=SCALE[Math.floor(Math.random()*SCALE.length)]*(Math.random()<.5?2:1);
    bell(t,f,.012*(level||1),Math.random()*1.6-.8,.6);},
  hero:function(pan){if(!live())return;bell(ctx.currentTime,783.99,.03,pan,1.1);},
  jobEnds:function(){if(!live())return;var t=ctx.currentTime;tone(t,98,1.6,{g:.14,a:.005});tone(t,196.5,.9,{g:.04});click(t,300,.12);},
  accelerator:function(){if(!live())return;var t=ctx.currentTime;[523.25,659.25,783.99,1046.5].forEach(function(f,i){bell(t+i*.06,f,.04,(i-1.5)*.3,1.6);});},
  converge:function(){if(!live())return;var t=ctx.currentTime;for(var i=0;i<14;i++){var f=[392,493.88,587.33][i%3]*(i%2?2:1);bell(t+i*.045+Math.random()*.02,f,.022,Math.random()*1.4-.7,1.8);}},
  dice:function(outcome){if(!live())return;var t=ctx.currentTime;for(var i=0;i<7;i++)click(t+i*.035+Math.random()*.02,2200+Math.random()*2400,.09*(1-i/9),Math.random()*.8-.4);
    var e=t+.3;if(outcome==='win'){tone(e,659.25,.5,{g:.07});tone(e+.08,987.77,.6,{g:.06});}else if(outcome==='lose'){tone(e,220,.4,{g:.08,to:180});}else{tone(e,440,.25,{g:.04});}}
};
})();
