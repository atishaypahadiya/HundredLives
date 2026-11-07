/* The valley: the 3D world every page of the site shares (docs/THEME.md).
   Noise, terrain and its rock-and-snow shader, sky, lights, clouds, the hut, ground scatter, the sheep,
   their trails and the camera rails. Needs three.js r128 loaded first (global THREE).

   var valley = createValley(canvas, {
     lives: 80,                        // a count: made-up paths from the hut to `corner` (strays go to their own targets)
                                       // or an array of {points: [[x, z], ...] one per week from week 0, stray: bool}
     hero: 31,                         // index of the life the chase shots follow (gold)
     strays: {31: [150, -130], ...},   // count mode: index -> [x, z] target; every other life walks to `corner`
     corner: [-150, 40],               // count mode: where the flock ends up
     weeks: 104,                       // weeks per life (the week counter runs 1..weeks)
     time: [.1, .95],                  // scroll range over which time runs from the first week to the last
     ghost: [.29, .36, .6, .68],       // others fade to ghosts from [0] to [1] and come back from [2] to [3]
     shots: [{p, pos, look}, ...]      // camera rails: pos and look are [x, y, z], 'hut', or 'chase' (pos) for the ghost cam
   });
   valley.update(progress)  // per animation frame: scroll progress 0..1 in; eases toward it, renders,
                            // and returns {progress (the eased value), u (life time 0..1), week}
   valley.resize()          // after the canvas changes size
*/
(function(){
var T=THREE;

/* ---------- noise ---------- */
function rng(s){return function(){s|=0;s=s+0x6D2B79F5|0;var t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;}}
var perm=[],R0=rng(7),i;for(i=0;i<256;i++)perm[i]=i;for(i=255;i>0;i--){var j=Math.floor(R0()*(i+1)),t=perm[i];perm[i]=perm[j];perm[j]=t;}for(i=0;i<256;i++)perm[i+256]=perm[i];
function fade(t){return t*t*t*(t*(t*6-15)+10);}
function grad(h,x,y){var g=h&7,u=g<4?x:y,v=g<4?y:x;return((g&1)?-u:u)+((g&2)?-2*v:2*v);}
function noise(x,y){var X=Math.floor(x)&255,Y=Math.floor(y)&255;x-=Math.floor(x);y-=Math.floor(y);var u=fade(x),v=fade(y),a=perm[X]+Y,b=perm[X+1]+Y;
 return (1-v)*((1-u)*grad(perm[a],x,y)+u*grad(perm[b],x-1,y))+v*((1-u)*grad(perm[a+1],x,y-1)+u*grad(perm[b+1],x-1,y-1));}
function fbm(x,y,o){var s=0,a=.5,f=1;for(var k=0;k<o;k++){s+=a*noise(x*f,y*f);f*=2.03;a*=.5;}return s;}
function ridged(x,y,o){var s=0,a=.5,f=1;for(var k=0;k<o;k++){var n=1-Math.abs(noise(x*f,y*f));s+=a*n*n;f*=2.1;a*=.5;}return s;}
function sm(a,b,x){x=Math.min(1,Math.max(0,(x-a)/(b-a)));return x*x*(3-2*x);}

/* ---------- terrain: a meadow bowl, green foothills, then real mountains ---------- */
function vrad(x,z){var dx=x/260,dz=(z+40)/190;return Math.sqrt(dx*dx+dz*dz)+fbm(x*.004,z*.004,3)*.35;}
function wallMask(x,z){return sm(0.9,1.6,vrad(x,z));} // 0 on the valley floor, 1 in the mountains
// value noise with analytic derivatives, and the "eroded" fbm that uses them (Quilez):
// octaves are damped where the slope is already steep, which carves ridges, spurs and gullies.
function hsh(ix,iy){return perm[(perm[ix&255]+iy)&255]/127.5-1;}
function noised(x,y){var ix=Math.floor(x),iy=Math.floor(y),fx=x-ix,fy=y-iy,ux=fx*fx*(3-2*fx),uy=fy*fy*(3-2*fy),dux=6*fx*(1-fx),duy=6*fy*(1-fy);
 var a=hsh(ix,iy),b=hsh(ix+1,iy),c=hsh(ix,iy+1),d=hsh(ix+1,iy+1),k=a-b-c+d;
 return [a+(b-a)*ux+(c-a)*uy+k*ux*uy, dux*((b-a)+k*uy), duy*((c-a)+k*ux)];}
function eroded(x,y,o){var a=0,b=1,dx=0,dy=0;for(var k=0;k<o;k++){var n=noised(x,y);dx+=n[1];dy+=n[2];a+=b*n[0]/(1+dx*dx+dy*dy);b*=.5;var nx=1.6*x-1.2*y,ny=1.2*x+1.6*y;x=nx;y=ny;}return a;}
function H(x,z){
 var floor=fbm(x*.006,z*.006,3)*5+fbm(x*.03,z*.03,2)*.8;
 var r=vrad(x,z);
 var hills=sm(.85,1.5,r)*(34+fbm(x*.0035+2,z*.0035,3)*70+fbm(x*.012,z*.012,2)*8);                       // rounded green foothills
 var dz=(z+40)/190, dl=Math.sqrt((x/260)*(x/260)+dz*dz)||1;
 var side=1-.72*sm(.05,.75,dz/dl);                                             // the camera side (south) stays low, the far side is the big range
 var M=sm(1.45,3.0,r)*side;                                                    // the massif rises over a long run, like real slopes
 var e=eroded(x*.0024+3.1,z*.0024-1.7,9)*.5+.5;                                // 0..1, gullies and spurs
 var mass=Math.max(0,fbm(x*.0014+4.1,z*.0014-2.3,3)*.9+.55);                 // broad massifs
 var cr=1-Math.abs(noise(x*.0032+1.3,z*.0032+5.9));                             // soft crestlines
 var peaks=Math.pow(mass,1.5)*520+e*200+cr*cr*140+ridged(x*.011,z*.011,3)*16;
 return floor+hills+M*peaks;
}
var GR=new T.Color('#3d6328'),GR2=new T.Color('#6a8338'),DRY=new T.Color('#8f8a55');
function buildLand(size,segs,hole,drop){
 var g=new T.PlaneGeometry(size,size,segs,segs);g.rotateX(-Math.PI/2);
 var pa=g.attributes.position,q;
 for(q=0;q<pa.count;q++){pa.setY(q,H(pa.getX(q),pa.getZ(q))-drop);}
 if(hole){var ix=g.index.array,keep=[];for(q=0;q<ix.length;q+=3){var inside=true;for(var t=0;t<3;t++){var v=ix[q+t];if(Math.abs(pa.getX(v))>hole||Math.abs(pa.getZ(v))>hole){inside=false;break;}}if(!inside)keep.push(ix[q],ix[q+1],ix[q+2]);}g.setIndex(keep);}
 g.computeVertexNormals();
 var cols=new Float32Array(pa.count*3),c=new T.Color();
 for(q=0;q<pa.count;q++){var x=pa.getX(q),y=pa.getY(q),z=pa.getZ(q),n1=fbm(x*.02,z*.02,3);
  c.copy(GR).lerp(GR2,sm(-.3,.4,n1)).lerp(DRY,sm(30,110,y)*.8);   // grass, browning as it climbs; rock and snow are painted per pixel
  cols[q*3]=c.r;cols[q*3+1]=c.g;cols[q*3+2]=c.b;}
 g.setAttribute('color',new T.BufferAttribute(cols,3));
 return g;
}
// per-pixel rock: strata bands, cliff colour, snow by height and slope, and a bump from 3D noise
function landMaterial(){
 var landMat=new T.MeshStandardMaterial({vertexColors:true,roughness:1,metalness:0});
 landMat.onBeforeCompile=function(sh){
  sh.vertexShader='varying vec3 vWP;varying vec3 vWN;\n'+sh.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvWP=(modelMatrix*vec4(transformed,1.)).xyz;vWN=normalize(mat3(modelMatrix)*objectNormal);');
  sh.fragmentShader='varying vec3 vWP;varying vec3 vWN;\n'+
  'float hs(vec3 p){p=fract(p*.3183099+.1);p*=17.;return fract(p.x*p.y*p.z*(p.x+p.y+p.z));}\n'+
  'float vn(vec3 x){vec3 i=floor(x),f=fract(x);f=f*f*(3.-2.*f);return mix(mix(mix(hs(i),hs(i+vec3(1,0,0)),f.x),mix(hs(i+vec3(0,1,0)),hs(i+vec3(1,1,0)),f.x),f.y),mix(mix(hs(i+vec3(0,0,1)),hs(i+vec3(1,0,1)),f.x),mix(hs(i+vec3(0,1,1)),hs(i+vec3(1,1,1)),f.x),f.y),f.z);}\n'+
  'float fb(vec3 p){float s=0.,a=.5;for(int i=0;i<5;i++){s+=a*vn(p);p=p*2.03+vec3(1.7,9.2,3.1);a*=.5;}return s;}\n'+
  'float rockAmt;float snowAmt;\n'+
  sh.fragmentShader.replace('#include <color_fragment>',
  '#include <color_fragment>\n'+
  'vec3 P=vWP;vec3 WN=normalize(vWN);float slope=1.-WN.y;float n=fb(P*.012);float n2=fb(P*.06);\n'+
  'float band=.5+.5*sin(P.y*.06+n*9.+P.x*.003);\n'+
  'vec3 rust=vec3(.52,.33,.26),ochre=vec3(.66,.53,.42),grey=vec3(.52,.5,.49),dark=vec3(.30,.24,.22);\n'+
  'vec3 rock=mix(rust,ochre,smoothstep(.25,.85,band)*.6);rock=mix(rock,grey,smoothstep(300.,650.,P.y+(n-.5)*200.)*.6);rock=mix(rock,dark,smoothstep(.5,.85,slope)*.3);\n'+
  'rock*=.88+.24*n2;\n'+
  'rockAmt=smoothstep(.22,.42,slope+(n-.5)*.35)*smoothstep(25.,70.,P.y);rockAmt=max(rockAmt,smoothstep(110.,190.,P.y+(n-.5)*70.));\n'+
  'diffuseColor.rgb=mix(diffuseColor.rgb,rock,rockAmt);\n'+
  'snowAmt=smoothstep(480.,560.,P.y+(n-.5)*160.)*smoothstep(.85,.45,slope+(n2-.5)*.4);\n'+
  'snowAmt=max(snowAmt,smoothstep(700.,780.,P.y)*.9);\n'+
  'diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.95,.96,.98),snowAmt);\n')
  .replace('#include <normal_fragment_maps>',
  '#include <normal_fragment_maps>\n'+
  '{float e=.6;vec3 q=vWP*vec3(.1,.03,.1);float h0=fb(q);vec3 g=vec3(fb(q+vec3(e,0,0))-h0,fb(q+vec3(0,e,0))-h0,fb(q+vec3(0,0,e))-h0)/e;\n'+
  ' vec3 q2=vWP*.4;float k0=vn(q2);vec3 g2=vec3(vn(q2+vec3(.3,0,0))-k0,vn(q2+vec3(0,.3,0))-k0,vn(q2+vec3(0,0,.3))-k0)/.3;\n'+
  ' vec3 WN=normalize(vWN);g=g*(.7*rockAmt+.2)+g2*.18*rockAmt;g-=dot(g,WN)*WN;\n'+
  ' normal=normalize(normal-(viewMatrix*vec4(g,0.)).xyz*(1.-snowAmt*.6));}\n');
 };
 return landMat;
}

function createValley(cv,opts){
 var renderer=new T.WebGLRenderer({canvas:cv,antialias:true});
 renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));
 renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;

 var scene=new T.Scene(), HAZE=new T.Color('#c9dbe6');
 scene.fog=new T.Fog(HAZE,500,3600);
 var cam=new T.PerspectiveCamera(42,1,0.5,6000);

 var landMat=landMaterial(), small=innerWidth<700;
 var land=new T.Mesh(buildLand(1800,small?340:560,0,0),landMat);land.receiveShadow=true;land.castShadow=true;scene.add(land);
 var far=new T.Mesh(buildLand(6000,small?160:260,880,3),landMat);far.receiveShadow=true;scene.add(far);

 /* ---------- sky, sun, clouds ---------- */
 var sky=new T.Mesh(new T.SphereGeometry(5000,32,16),new T.ShaderMaterial({side:T.BackSide,depthWrite:false,fog:false,
  uniforms:{top:{value:new T.Color('#4f8fd0')},hor:{value:HAZE}},
  vertexShader:'varying vec3 p;void main(){p=normalize(position);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
  fragmentShader:'uniform vec3 top,hor;varying vec3 p;void main(){float h=clamp(p.y*2.2,0.,1.);gl_FragColor=vec4(mix(hor,top,pow(h,.7)),1.);}'}));
 scene.add(sky);
 scene.add(new T.HemisphereLight('#d6e6f5','#4d5530',0.7));
 var sun=new T.DirectionalLight('#fff0d8',0.9);sun.position.set(-260,320,180);sun.castShadow=true;
 sun.shadow.mapSize.set(2048,2048);var sc=sun.shadow.camera;sc.left=-420;sc.right=420;sc.top=420;sc.bottom=-420;sc.near=10;sc.far=1400;sun.shadow.bias=-0.0006;
 scene.add(sun);scene.add(sun.target);
 // One seeded stream for everything random below, drawn in a fixed order (clouds, grass, flowers, rocks, lives),
 // so the same options always build the same valley.
 var cloudMat=new T.MeshLambertMaterial({color:'#ffffff',emissive:'#9fb3c4',emissiveIntensity:.35,transparent:true,opacity:.8,fog:false});
 var R=rng(21),i;
 for(i=0;i<14;i++){var g=new T.Group(),cx=(R()-.5)*3000,cz=-900-R()*1800,cy=900+R()*400;
  for(var k=0;k<7;k++){var s=new T.Mesh(new T.SphereGeometry(1,12,8),cloudMat);s.scale.set(80+R()*90,22+R()*18,60+R()*60);s.position.set((R()-.5)*240,R()*20,(R()-.5)*100);g.add(s);}
  g.position.set(cx,cy,cz);scene.add(g);}

 /* ---------- the hut (the referee) ---------- */
 var HUT=new T.Vector3(10,0,-20);HUT.y=H(HUT.x,HUT.z);
 var hut=new T.Group();
 var wall=new T.Mesh(new T.BoxGeometry(7,3.2,5),new T.MeshLambertMaterial({color:'#ece6d8'}));wall.position.y=1.6;
 var roof=new T.Mesh(new T.CylinderGeometry(0,5.2,2.4,4,1),new T.MeshLambertMaterial({color:'#4f7fa6'}));roof.rotation.y=Math.PI/4;roof.scale.set(1.05,1,.75);roof.position.y=4.4;
 var door=new T.Mesh(new T.BoxGeometry(1.2,2,.1),new T.MeshLambertMaterial({color:'#3a2d22'}));door.position.set(0,1,2.52);
 [wall,roof].forEach(function(m){m.castShadow=true;m.receiveShadow=true;});
 hut.add(wall,roof,door);hut.position.copy(HUT);hut.rotation.y=.3;scene.add(hut);

 /* ---------- ground detail: grass tufts, flowers, rocks ---------- */
 var dummy=new T.Object3D();
 function scatter(geom,mat,n,area,fn){var im=new T.InstancedMesh(geom,mat,n),col=new T.Color();
  for(var q=0;q<n;q++){var x=(R()-.5)*area[0]+area[2],z=(R()-.5)*area[1]+area[3];if(wallMask(x,z)>.25){q--;continue;}fn(dummy,x,z,col);dummy.updateMatrix();im.setMatrixAt(q,dummy.matrix);if(im.setColorAt)im.setColorAt(q,col);}
  scene.add(im);return im;}
 var blade=new T.ConeGeometry(.05,.45,3);blade.translate(0,.22,0);
 scatter(blade,new T.MeshLambertMaterial({color:'#ffffff'}),60000,[380,300,-30,-10],function(d,x,z,col){
  d.position.set(x,H(x,z)-.05,z);d.rotation.set((R()-.5)*.5,R()*6,(R()-.5)*.5);var s=.6+R()*.8;d.scale.set(s,s*(.6+R()*.9),s);
  col.set(R()<.5?'#5d8a30':'#7ea443').offsetHSL(0,0,(R()-.5)*.08);});
 scatter(new T.SphereGeometry(.12,5,4),new T.MeshLambertMaterial({color:'#ffffff'}),5000,[340,280,-40,0],function(d,x,z,col){
  d.position.set(x,H(x,z)+.12,z);d.scale.setScalar(.4+R()*.5);col.set(R()<.6?'#f4e27a':'#fbf7f0');});
 var rockG=new T.DodecahedronGeometry(1,0);
 var rocks=scatter(rockG,new T.MeshLambertMaterial({color:'#ffffff'}),220,[420,340,-40,0],function(d,x,z,col){
  d.position.set(x,H(x,z),z);d.rotation.set(R()*3,R()*3,R()*3);var s=.4+Math.pow(R(),3)*3.5;d.scale.set(s*1.3,s*.7,s);col.set('#9c9184').offsetHSL(0,0,(R()-.5)*.1);});
 rocks.castShadow=true;

 /* ---------- lives: one path per life over the weeks ---------- */
 var WEEKS=opts.weeks||104, HERO=opts.hero, lives=[];
 if(typeof opts.lives==='number'){ // made-up paths: wander from the hut, then commit to a target
  var strays=opts.strays||{}, CORNER=new T.Vector3(opts.corner[0],0,opts.corner[1]);
  for(i=0;i<opts.lives;i++){
   var stray=strays.hasOwnProperty(i);
   var target=stray? new T.Vector3(strays[i][0],0,strays[i][1]) : CORNER.clone().add(new T.Vector3((R()-.5)*55,0,(R()-.5)*45));
   var p=HUT.clone().add(new T.Vector3((R()-.5)*8,0,6+R()*6)), v=new T.Vector3(), pts=[];
   var commit=stray? .2+R()*.2 : .1+R()*.4, wander=1.6+R()*1.2, ph=R()*100;
   for(var w=0;w<=WEEKS;w++){
    pts.push(new T.Vector3(p.x,0,p.z));
    var f=w/WEEKS, pull=sm(commit*.5,commit+.35,f);
    var to=target.clone().sub(p);var dist=to.length();to.normalize();
    var ang=noise(ph+w*.09,i*.37)*2.4;
    var drift=new T.Vector3(Math.cos(ang),0,Math.sin(ang)).multiplyScalar(wander*(1-pull*.7));
    v.lerp(to.multiplyScalar(Math.min(dist*.15,4.2)*pull).add(drift),.35);
    p.add(v);
   }
   lives.push({stray:stray,curve:new T.CatmullRomCurve3(pts,false,'centripetal'),phase:R()*6});
  }
 }else{ // given paths, e.g. from positions.json
  opts.lives.forEach(function(L){
   var pts=L.points.map(function(q){return new T.Vector3(q[0],0,q[1]);});
   lives.push({stray:!!L.stray,curve:new T.CatmullRomCurve3(pts,false,'centripetal'),phase:R()*6});
  });
 }
 function lifeAt(L,u){ // u in [0,1]
  var p=L.curve.getPointAt(Math.min(.9999,Math.max(0,u)));p.y=H(p.x,p.z);return p;}
 /* trails: flat ribbons draped on the ground, drawn up to the current week */
 var SEG=500, trails=[];
 function ribbon(L,wd,lift){var rib=[],ix=[];for(var s=0;s<=SEG;s++){var t=s/SEG*.9999,a=L.curve.getPointAt(t),b=L.curve.getTangentAt(t),nx=-b.z,nz=b.x,l=Math.hypot(nx,nz)||1;
   rib.push(a.x+nx/l*wd,H(a.x+nx/l*wd,a.z+nz/l*wd)+lift,a.z+nz/l*wd,a.x-nx/l*wd,H(a.x-nx/l*wd,a.z-nz/l*wd)+lift,a.z-nz/l*wd);if(s<SEG){var o=s*2;ix.push(o,o+1,o+2,o+1,o+3,o+2);}}
  var g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(rib,3));g.setIndex(ix);g.setDrawRange(0,0);return g;}
 lives.forEach(function(L,idx){
  var isHero=idx===HERO;
  var m=new T.MeshBasicMaterial({color:isHero?'#ffb938':(L.stray?'#ffd98a':'#ffffff'),transparent:true,opacity:isHero?1:(L.stray?.85:.5),depthWrite:false,side:T.DoubleSide,
   polygonOffset:true,polygonOffsetFactor:-2,polygonOffsetUnits:-2});
  var mesh=new T.Mesh(ribbon(L,isHero?.6:(L.stray?.6:.32),isHero?.22:.18),m);mesh.renderOrder=isHero?3:2;scene.add(mesh);trails.push(mesh);
 });

 /* ---------- sheep ---------- */
 var woolG=new T.IcosahedronGeometry(1,1), headG=new T.SphereGeometry(1,10,8), legG=new T.CylinderGeometry(.09,.08,1,5);legG.translate(0,-.5,0);
 var woolM=new T.MeshLambertMaterial({color:'#f3eee3',transparent:true}), faceM=new T.MeshLambertMaterial({color:'#2b2420',transparent:true});
 var heroWool=new T.MeshLambertMaterial({color:'#fff6e0',emissive:'#5a3a00',emissiveIntensity:.18});
 var heroFace=new T.MeshLambertMaterial({color:'#2b2420'});
 function makeSheep(hero){
  var g=new T.Group(),body=new T.Group();g.add(body);
  var wm=hero?heroWool:woolM,fm=hero?heroFace:faceM;
  var blobs=[[0,0,0,1],[.55,.1,0,.82],[-.55,.08,0,.85],[0,.35,.25,.7],[0,.3,-.25,.7],[.3,.4,0,.6],[-.3,.38,0,.62]];
  blobs.forEach(function(b){var m=new T.Mesh(woolG,wm);m.position.set(b[0],b[1],b[2]);m.scale.set(b[3]*.75,b[3]*.62,b[3]*.62);m.castShadow=true;body.add(m);});
  var head=new T.Mesh(headG,fm);head.scale.set(.32,.3,.24);head.position.set(1.05,.25,0);head.castShadow=true;body.add(head);
  var ear1=new T.Mesh(headG,fm);ear1.scale.set(.06,.04,.16);ear1.position.set(.98,.38,.24);var ear2=ear1.clone();ear2.position.z=-.24;body.add(ear1,ear2);
  var legs=[];[[.45,.22],[.45,-.22],[-.45,.22],[-.45,-.22]].forEach(function(q){var l=new T.Mesh(legG,fm);l.position.set(q[0],-.35,q[1]);l.scale.y=.75;body.add(l);legs.push(l);});
  body.position.y=1.1;g.userData={body:body,head:head,legs:legs};g.scale.setScalar(1.25);scene.add(g);return g;
 }
 lives.forEach(function(L,idx){L.mesh=makeSheep(idx===HERO);});

 /* ---------- camera rails ---------- */
 var hero=lives[HERO], shots=opts.shots;
 function point(v){return v==='hut'?HUT.clone():new T.Vector3(v[0],v[1],v[2]);}
 function chase(u){
  var h=lifeAt(hero,u), ahead=lifeAt(hero,Math.min(1,u+.025)), back=lifeAt(hero,Math.max(0,u-.03));
  var dir=ahead.clone().sub(back);dir.y=0;if(dir.lengthSq()<1e-4)dir.set(1,0,0);dir.normalize();
  var side=new T.Vector3(-dir.z,0,dir.x);
  var pos=h.clone().addScaledVector(dir,-13).addScaledVector(side,5);pos.y=Math.max(pos.y,H(pos.x,pos.z))+5.5;
  var look=h.clone().addScaledVector(dir,10);look.y+=1.2;
  return [pos,look];
 }
 function evalShot(s,u){if(s.pos==='chase'){return chase(u);}return [point(s.pos),point(s.look)];}
 function camAt(p,u){
  for(var k=0;k<shots.length-1;k++){if(p<=shots[k+1].p)break;}
  var a=shots[k],b=shots[Math.min(k+1,shots.length-1)],f=b.p===a.p?0:(p-a.p)/(b.p-a.p);f=f*f*(3-2*f);
  var A=evalShot(a,u),B=evalShot(b,u);
  var P=A[0].lerp(B[0],f);P.y=Math.max(P.y,H(P.x,P.z)+(P.y>60?40:3));return [P,A[1].lerp(B[1],f)];
 }
 var TIME=opts.time||[0,1], GHOST=opts.ghost;
 function timeAt(p){ // scroll -> life progress u. Time stands still before TIME[0] (the aerial intro).
  return sm(TIME[0],TIME[1],p)*.999;
 }

 /* ---------- per frame ---------- */
 var cur=0,camPos=new T.Vector3(),camLook=new T.Vector3(),first=true,clock=new T.Clock();
 function resize(){var w=cv.clientWidth,h=cv.clientHeight;if(!w||!h)return;renderer.setSize(w,h,false);cam.aspect=w/h;cam.fov=w<700?58:42;cam.updateProjectionMatrix();}
 function update(target){
  var dt=Math.min(.05,clock.getDelta()),time=clock.elapsedTime;
  cur+=(target-cur)*(1-Math.exp(-dt*5));if(first)cur=target;
  var u=timeAt(cur);
  var ghost=GHOST?sm(GHOST[0],GHOST[1],cur)*(1-sm(GHOST[2],GHOST[3],cur)):0; // others fade to ghosts while we follow one
  woolM.opacity=1-ghost*.62;faceM.opacity=woolM.opacity;woolM.depthWrite=ghost<.05;faceM.depthWrite=woolM.depthWrite;
  lives.forEach(function(L,idx){
   var lu=u, p=lifeAt(L,lu), q=lifeAt(L,Math.min(1,lu+.004));
   var m=L.mesh;m.position.copy(p);
   var dx=q.x-p.x,dz=q.z-p.z;if(dx*dx+dz*dz>1e-6)m.rotation.y=Math.atan2(-dz,dx);
   var moving=Math.abs(target-cur)>.0005, ud=m.userData, ph=time*9+L.phase;
   ud.body.position.y=1.1+(moving?Math.abs(Math.sin(ph))*.08:0);
   ud.head.position.y=moving?.25:.25-(.5+.5*Math.sin(time*1.3+L.phase))*.35; // graze when still
   ud.legs.forEach(function(l,n){l.rotation.z=moving?Math.sin(ph+(n%2?Math.PI:0))*.45:0;});
   var cnt=Math.max(0,Math.round(u*SEG));trails[idx].geometry.setDrawRange(0,cnt*6);
   if(idx!==HERO&&!L.stray)trails[idx].material.opacity=.5*(1-ghost*.35);
  });
  var c=camAt(cur,u);
  if(first){camPos.copy(c[0]);camLook.copy(c[1]);first=false;}else{camPos.lerp(c[0],1-Math.exp(-dt*6));camLook.lerp(c[1],1-Math.exp(-dt*6));}
  cam.position.copy(camPos);cam.lookAt(camLook);
  sun.target.position.set(camLook.x,0,camLook.z);sun.position.set(camLook.x-260,430,camLook.z+140);
  renderer.render(scene,cam);
  return {progress:cur,u:u,week:Math.max(1,Math.round(1+u*(WEEKS-1)))};
 }
 return {update:update,resize:resize};
}
createValley.terrain={height:H,wallMask:wallMask}; // for checks that points sit on the valley floor (analysis/positions.py)
window.createValley=createValley;
})();
