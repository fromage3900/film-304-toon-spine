// Film-owned surface treatment. UV anchored, deterministic, no Time input.
// Inputs are linear color; coverage/masks are normalized separately from HDR color.
float2 uv = UV;
float seed = clamp(Seed, 0.0, 65535.0);
float freq = clamp(Frequency, 1.0, 512.0);
float angle = clamp(Rotation, -360.0, 360.0) * 0.01745329252;
float2 q = float2(uv.x*cos(angle)-uv.y*sin(angle),
                  uv.x*sin(angle)+uv.y*cos(angle)) * freq;
float2 cell = floor(q);
float2 f = frac(q)-0.5;
float footprint = max(length(float2(ddx(q.x),ddy(q.x))),
                      length(float2(ddx(q.y),ddy(q.y))));
float aa = max(0.001, min(0.5, footprint));
float fade = 1.0-smoothstep(0.35, 1.0, footprint);
float coverage = saturate(Coverage);
float radius = sqrt(coverage*0.31830988618);
float dots = 1.0-smoothstep(radius-aa, radius+aa, length(f));
// Exact artist endpoints: zero coverage is clean, full coverage is solid ink.
dots = coverage <= 0.0 ? 0.0 : (coverage >= 1.0 ? 1.0 : dots);
// Under-resolved dots converge towards average coverage instead of crawling.
dots = lerp(coverage, dots, fade);
float luma = max(0.0, dot(BaseColor, float3(0.2126,0.7152,0.0722)));
float shadow = pow(saturate(1.0-ShadowDriver),clamp(ShadowContrast,0.1,8.0));
float inkGate = lerp(1.0,shadow,saturate(ShadowWeight));
float3 color = lerp(BaseColor,BaseColor*max(InkTint,0.0),
                    saturate(HalftoneStrength)*dots*inkGate);
// 4x4 Bayer, generated from the standard 2x2 recursion, no texture dependency.
int2 p = int2(floor(q));
int x = p.x & 3; int y = p.y & 3;
int low = ((x & 1) ^ (y & 1))*2 + (y & 1);
int high = (((x >> 1) & 1) ^ ((y >> 1) & 1))*2 + ((y >> 1) & 1);
float bayer = (float(low*4+high)+0.5)/16.0;
float noise = frac(sin(dot(cell+seed,float2(127.1,311.7)))*43758.5453);
float threshold = lerp(bayer,noise,step(0.5,clamp(DitherMode,0.0,1.0)));
float bands = floor(clamp(DitherBands,2.0,32.0)+0.5);
float3 quantized = floor(max(color,0.0)*bands+threshold)/bands;
color = lerp(color,quantized,saturate(DitherStrength)*fade);
// Watercolour: restrained pigment granulation and pooling at tonal gradients.
// This is a surface approximation, not simulation or neighboring texture resampling.
float paperFreq = clamp(PaperScale,1.0,1024.0);
float2 paperUV = uv*paperFreq;
float paper = 0.5+0.25*sin(paperUV.x*6.2831853+sin(paperUV.y*2.7+seed))
                   +0.25*sin(paperUV.y*5.41+sin(paperUV.x*1.7));
float paperFootprint = max(length(ddx(paperUV)),length(ddy(paperUV)));
paper = lerp(paper,0.5,smoothstep(0.35,1.0,paperFootprint));
float grain = (paper-0.5)*saturate(Granulation);
float pooling = saturate(fwidth(luma)*clamp(Pooling,0.0,8.0));
float3 wash = max(color*(1.0+grain-pooling*0.35),0.0);
wash = lerp(wash,lerp(wash,max(PaperTint,0.0),0.2),saturate(PaperLift));
return max(lerp(color,wash,saturate(WatercolourStrength)),0.0);
