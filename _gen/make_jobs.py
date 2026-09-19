# Builds jobs.json — one entry per Gemini render.
#   name  : file stem, lands in _src/<name>.png
#   w,h   : the layer's box in the 1280x900 design space (drives aspect + padding)
#   fit   : pad  = key it out, pad to the box ratio  (default, for cut-outs)
#           cover= crop to the box ratio             (wide bands, backdrop plates)
#           bg   = full-bleed background, no keying
#   keys  : 1 = green only, 2 = green outside + magenta slots inside
import json

STYLE = ("Cinematic 3D product render, photoreal materials, dramatic directional "
         "rim light, high contrast. The subject is centred and fills about 90% of the frame.")

KEY = ("Everything outside the subject must be completely flat, uniform, solid #00FF00 pure "
       "green: one single colour, no gradient, no shadow, no reflection, no floor, no ground, "
       "no background scene, no vignette. Nothing in the subject itself may be green or "
       "greenish. No text, no writing, no numbers, no letters, no brand name, no logo, "
       "no watermark, no signature.")

ONE = ("Draw exactly ONE single subject. Do not draw it twice, no duplicate, no turnaround sheet. "
       "Reply with the picture only. Do not describe it, do not comment on it, do not explain "
       "what you changed or point out anything about the framing.")

def cut(name, w, h, body, shape="", keys=1, fit="pad"):
    ratio = w / h
    if shape:
        pass
    elif ratio > 2.2:  shape = "Extremely wide short horizontal banner image."
    elif ratio > 1.25: shape = "Wide landscape image."
    elif ratio < 0.45: shape = "Extremely tall narrow vertical portrait image."
    elif ratio < 0.8:  shape = "Tall vertical portrait image."
    else:              shape = "Square image."
    return dict(name=name, w=w, h=h, fit=fit, keys=keys,
                prompt="\n\n".join([body.strip(), shape, STYLE, ONE, KEY]))

def bg(name, body):
    return dict(name=name, w=1600, h=900, fit="bg", keys=0,
                prompt=body.strip() + "\n\nWide cinematic 16:9 photograph, film grain, "
                "rich colour grading. No text, no logo, no watermark, no people looking at camera.")

J = []

# ---------------------------------------------------------------- 00 blackout
J += [bg("bg-blackout", """
Looking down a narrow Beirut residential street at night during a total power cut.
Concrete apartment buildings with cluttered balconies crowd both sides, and every
single window is dark. The only light is a weak warm orange glow from two or three
candle-lit rooms far down the street, and a faint cold blue moonlight on the asphalt.
Heavy blue-black shadow, deep contrast, the far end of the street softly out of focus.
"""),

cut("skyline", 1360, 470, """
A continuous row of Beirut apartment blocks seen from across the city at night during a
blackout, photographed dead straight on so it reads as a flat wall of buildings of slightly
different heights. Cluttered rooftops with black plastic water tanks, satellite dishes and
antenna masts breaking the top edge. Every window is dark and unlit. Rendered almost as a
near-black silhouette, with only a thin cold blue rim of moonlight along the upper edges.
""", fit="cover"),

cut("tower_l", 250, 560, """
A single tall narrow Beirut apartment tower, about twelve storeys, seen dead straight on from
the front, unlit at night during a power cut. Weathered grey concrete, rows of small balconies
with laundry lines and rusting air-conditioner units, a black plastic water tank and a satellite
dish on the roof. Every window dark, only a cold blue moonlight rim down the left edge.
The tower stands upright and fills the full height of the frame.
"""),

cut("tower_r", 236, 500, """
A single Beirut apartment tower, about ten storeys, seen dead straight on from the front, unlit
at night during a power cut. Sand-coloured render stained with damp, a lift shaft box on the
roof, rows of shuttered balconies, a tangle of cables down one side. Every window dark, only a
cold blue moonlight rim down the right edge. It stands upright and fills the full height of the frame.
"""),

cut("wires", 1400, 210, """
A chaotic tangle of Lebanese overhead electricity cables strung between two leaning utility
poles: dozens of black wires sagging in messy loops, bundles taped together at the middle,
several ends hanging loose, a small transformer can bolted to one pole. Seen dead straight on.
Near-black cables with a thin cold blue moonlight highlight along their upper edges.
""", fit="cover"),

cut("bulb", 84, 146, """
A single bare incandescent light bulb hanging straight down from a short length of black
twisted flex cable, seen from the side, switched OFF and completely dark. Clear glass envelope,
visible cold grey tungsten filament inside, brass screw base. Cold blue rim light only.
"""),

cut("meter", 146, 184, """
An old grimy Lebanese electricity meter, seen dead straight on from the front. A scratched
grey-white plastic casing with a small glass window showing black mechanical number dials and a
red rotating disc, two screw terminals under a cover at the bottom, and a lead seal on a twisted
wire. Worn, dusty, unlit and dead. Cold dim light.
"""),

cut("moteur", 322, 232, """
A battered diesel generator of the kind that powers a Lebanese neighbourhood: a rusted
yellow-and-grey steel canopy on a skid frame, a fat exhaust pipe elbowing up out of the top,
a fuel cap, a control panel of dead unlit gauges, a pull handle, and oil stains and rust streaks
running down the sides. Three-quarter front view. Grimy and industrial.
"""),

cut("candle", 64, 148, """
A single white household candle burning, seen from the side, standing on nothing. Melted wax
running down one side, a small warm orange teardrop flame at the top with a soft halo close
around it. The warm orange light falls on the wax; everything else is dark. The glow must fade
to nothing well inside the frame.
""")]

# ------------------------------------------------------------------ 01 panels
J += [bg("bg-panels", """
A bright Beirut rooftop at midday looking out over the city towards the Mediterranean. Clear
deep blue sky with a few thin white clouds, hazy pale buildings receding into the distance, the
sea a bright band on the horizon. Strong hard overhead sunlight, crisp shadows, slight heat haze.
"""),

cut("sun", 226, 226, """
The sun as a brilliant white-hot disc in a clear sky seen through a camera lens: a round core of
pure white light with a warm golden corona bleeding outward and a few soft concentric lens-flare
rings. The disc is centred, and the glow fades completely to nothing well inside the frame so
there is a clean border of plain flat background all the way around it.
"""),

cut("cloud", 306, 122, """
A single small white cumulus cloud seen from the side, sunlit from the upper right, with bright
white billowing tops and soft grey-blue undersides. Clean crisp rounded edges, one solid shape,
never fine wispy see-through tendrils.
"""),

cut("roof", 1360, 240, """
The flat concrete roof deck of a Beirut apartment building at midday, seen from a low angle dead
straight on: a pale sun-bleached concrete slab running the full width, a low parapet wall behind
it, scattered grit, a rusted rebar stub and a drain. Strong midday sunlight from above with a
crisp hard shadow under the parapet.
""", fit="cover"),

cut("panel_a", 566, 356, """
An array of six solar panels bolted together as one block: six monocrystalline photovoltaic
modules in two rows of three, deep blue-black cells with fine silver busbar lines in a neat grid,
slim anodised aluminium frames. Seen from a low three-quarter front angle so the whole array
reads as one rectangular slab. Bright midday sun, a hard white specular streak sliding across the
glass, crisp reflections of blue sky in the cells.
"""),

cut("panel_b", 338, 226, """
An array of four solar panels bolted together as one block: four monocrystalline photovoltaic
modules in two rows of two, deep blue-black cells with fine silver busbar lines, slim anodised
aluminium frames. Seen from a low three-quarter front angle from slightly further right so the
array reads as one rectangular slab. Bright midday sun, hard specular highlight across the glass.
"""),

cut("bracket", 430, 96, """
A solar mounting rail assembly: one long extruded aluminium rail carried on three short
triangular tilt legs bolted down to flat concrete feet, with stainless steel module clamps spaced
along the top of the rail. Seen dead straight on from the side. Bright midday sunlight, clean
industrial hardware, sharp machined edges.
"""),

cut("bird", 90, 54, """
A single pigeon in flight seen from the side, wings spread wide mid-beat, grey and white
feathers catching bright midday sun from above.
""")]

# ---------------------------------------------------------------- 02 inverter
J += [bg("bg-inverter", """
The interior of a Lebanese building service room lit by one warm work lamp: bare grey plaster
walls, a scuffed concrete floor, a distribution board and a coil of conduit on the far wall,
dust in the air. Warm amber pool of light falling from the upper left, the corners deep in shadow.
"""),

cut("wall", 940, 716, """
A plain interior wall of a service room seen dead straight on and perfectly flat: bare grey
skim-coat plaster with a faint trowel texture, a couple of old screw holes and a light scuff
near one edge. Softly lit from the upper left with warm amber light, the corners a little darker.
""", keys=0, fit="cover"),

cut("cable_in", 268, 150, """
A thick black armoured electrical cable coming down from the top left and bending away to the
right, its cut end stripped back to show three insulated conductors coloured brown, blue and
grey, each ending in a short length of bare bright copper. Seen dead straight on.
"""),

cut("inv_body", 424, 524, """
A wall-mounted hybrid solar inverter with its front cover removed, seen perfectly flat and dead
straight on from the front. A rectangular dark charcoal cast-aluminium chassis, clearly taller
than it is wide, with deep vertical cooling fins down both outer sides, softly rounded corners,
and a row of cable glands along the bottom edge.

On its front face there are exactly TWO openings: in the UPPER HALF one wide horizontal
rectangular display recess, and in the LOWER HALF one large circular fan opening. Both the
rectangular recess and the circular opening are filled with completely flat, uniform, solid
#FF00FF magenta: one single colour, no gradient, no reflection, no detail, no grille, nothing
at all drawn inside them. The two magenta shapes do not touch each other.
""", keys=2),

cut("inv_cover", 424, 524, """
The loose front cover panel of a wall-mounted hybrid solar inverter, on its own and detached:
a flat dark charcoal anodised aluminium plate, clearly taller than it is wide, with rounded
corners, a brushed finish, a rectangular window cut-out in the upper half, a round vented grille
in the lower half, and four small countersunk screw holes. Seen at a slight three-quarter angle
so it reads as a separate loose panel with a visible edge thickness.
"""),

cut("inv_screen", 284, 152, """
A rectangular backlit LCD panel out of a solar inverter, seen perfectly flat and dead straight on
and filling the frame. Dark glass with a soft warm amber backlight glowing through it, showing a
row of abstract vertical bar-graph blocks and one large seven-segment style block shape. The
shapes are purely abstract with no readable words, letters or numbers anywhere.
"""),

cut("fan", 168, 168, """
A circular axial cooling fan seen perfectly flat and dead straight on from the front: seven
curved black plastic blades around a round central hub, set inside a black circular housing ring.
Fine dust on the blade edges, a cold specular highlight along the top of the ring.
"""),

cut("bracket_i", 472, 70, """
A galvanised steel wall-mounting bracket for an inverter: one long flat Z-folded steel rail with
a row of keyhole slots punched along it and two bolt holes at each end. Seen dead straight on
from the front. Bright zinc finish with a faint spangle.
"""),

cut("cable_out", 300, 170, """
Two thick black electrical cables leaving towards the right and curving down, bundled together
with a spiral wrap, each ending in a crimped copper lug, one with a red heat-shrink collar and
one with a black one. Seen dead straight on.
""")]

# ----------------------------------------------------------------- 03 battery
J += [bg("bg-battery", """
A dim technical room housing an energy storage system: a smooth dark concrete wall, a run of
cable tray overhead, a cold teal-green ambient glow from equipment out of shot, and one soft
pool of light on the floor. Very dark, moody, deep shadow, sparse and clean.
"""),

cut("rack", 494, 654, """
An empty open 19-inch equipment rack frame seen perfectly flat and dead straight on from the
front: two vertical black powder-coated steel posts with rows of square mounting holes punched
down them, joined by a top and a bottom rail, standing on four short feet. Clearly taller than
it is wide.

Inside the frame, stacked one above the other, are exactly FOUR rectangular slot openings that
each span the full width between the two posts: a SHORT thin one at the top, and below it THREE
TALLER openings of equal height, with a narrow gap between each. All four openings are filled
with completely flat, uniform, solid #FF00FF magenta: one single colour, no gradient, no
reflection, no equipment, nothing at all drawn inside them. The four magenta rectangles never
touch each other.
""", keys=2),

cut("bms", 438, 86, """
The front face of a battery management unit, seen perfectly flat and dead straight on and filling
the frame: a wide, short, slim black anodised aluminium panel with a row of small round indicator
LEDs glowing cyan along the left end, two recessed buttons, a small dark display window, and a
band of fine ventilation slots along the right end.
"""),

cut("cell", 438, 130, """
The front face of a rack-mounted lithium iron phosphate battery module, seen perfectly flat and
dead straight on and filling the frame: a wide, short, slim dark navy-black brushed metal panel
with two chunky recessed carry handles at the ends, a strip of fine ventilation slots across the
middle, and one small round indicator lamp glowing cyan.
"""),

cut("led_bar", 52, 430, """
A tall narrow vertical state-of-charge indicator standing upright: a slim matte black strip
holding a stack of twelve short glowing horizontal segments, the lower nine lit bright cyan-white
and the top three dark and unlit. The glow stays tight to each segment and fades to nothing well
inside the frame.
"""),

cut("cable_b", 258, 190, """
Two heavy battery cables, one red and one black, entering from the left and curving down to the
right, thick insulated copper with crimped ring terminals on the ends and a cable tie holding
them together. Seen dead straight on.
"""),

cut("breaker", 180, 150, """
A DC circuit breaker enclosure seen dead straight on from the front: a small grey plastic box
holding two double-pole breakers side by side with black toggle switches flipped up, behind a
clear polycarbonate hinged cover with four corner screws.
""")]

# ------------------------------------------------------------------ 04 onreal
J += [bg("bg-onreal", """
A quiet Beirut residential street at night, fully lit and alive: warm golden light spilling from
apartment windows up and down both sides, a street lamp throwing a soft pool on the asphalt,
jacaranda branches overhead, the sky a deep clean navy blue. Warm, calm, prosperous, cinematic.
"""),

cut("moon", 136, 136, """
A full moon high in a clear night sky seen through a long lens: a pale silver-white disc with
visible craters and dark maria, and a faint cool halo sitting tight around it that fades
completely to nothing well inside the frame.
"""),

cut("street", 1360, 180, """
A stretch of Beirut asphalt street and its kerb at night, seen from a low angle dead straight on
and running the full width: worn dark asphalt with patches and a faded white line, a concrete
kerb, and a strip of dusty pavement behind it. Warm amber light spills across it from above,
leaving long soft reflections on the asphalt.
""", fit="cover"),

cut("house", 716, 632, """
A small Lebanese family house seen perfectly flat and dead straight on from the front at night:
two storeys of warm sand-coloured render with stone quoins at the corners, a flat concrete roof
with a low parapet, an arched front door with a stone surround at ground level, and a balcony
with a wrought iron railing across the upper floor. Warm night lighting washing the walls.

On the front facade there are exactly FOUR rectangular windows: THREE side by side in an evenly
spaced row across the UPPER floor, and ONE more centred below them on the ground floor. All four
windows are filled with completely flat, uniform, solid #FF00FF magenta: one single colour, no
gradient, no glass, no reflection, no curtain, no glazing bars, nothing at all drawn inside them.
All four magenta rectangles are exactly the same size and shape, and none of them touch anything.
""", keys=2),

cut("roof_pv", 470, 130, """
A row of four solar panels mounted on a low rooftop rail, seen from a low front angle so the row
reads as one long slim slab: deep blue-black monocrystalline cells with fine silver grid lines,
slim aluminium frames, tilted slightly back. Night time, lit by cool moonlight from above with a
faint warm glow rising from below.
"""),

cut("window", 132, 118, """
A single lit window at night seen perfectly flat and dead straight on and filling the frame: a
white painted wooden window frame divided into four panes, warm golden light glowing out from
inside, and the hint of a curtain edge and a warm interior wall visible behind the glass.
"""),

dict(name="icons", w=0, h=0, fit="sheet", keys=1, slices=["ac", "wifi", "fridge"], prompt="\n\n".join(["""
Three separate household objects arranged in one horizontal row, clearly separated with a wide
gap of plain flat background between them, none of them touching or overlapping each other:

FIRST, on the left, a white wall-mounted split air-conditioner indoor unit seen dead straight on
from the front, its louvre open and one small status light glowing cyan.
SECOND, in the middle, a small white wifi router seen dead straight on from the front, standing
on its base with two upright antennas and a row of small blue indicator lights across it.
THIRD, on the right, a tall white two-door refrigerator seen dead straight on from the front,
with slim vertical brushed steel handles and a faint warm light leaking from the door seam.

All three are drawn in the same style at the same quality, lit the same way from the upper left
with a warm night light, with a cool rim light down their right edges.
""".strip(), STYLE, KEY]))]

json.dump(J, open("jobs.json", "w"), indent=1)
print(len(J), "jobs")
for j in J:
    print(f"  {j['name']:<12} {j['fit']:<6} keys={j['keys']} {j['w']}x{j['h']}")
