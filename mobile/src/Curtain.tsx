import React, { useEffect, useMemo, useState } from "react";
import { StyleSheet, useWindowDimensions } from "react-native";
import {
  Canvas,
  Circle,
  Fill,
  Group,
  Image as SkiaImage,
  LinearGradient,
  Oval,
  Path,
  RoundedRect,
  Skia,
  Text as SkiaText,
  type SkFont,
  useClock,
  useFont,
  useImage,
  vec,
} from "@shopify/react-native-skia";
import {
  Easing,
  type SharedValue,
  useDerivedValue,
  useSharedValue,
  withDelay,
  withTiming,
} from "react-native-reanimated";
import { scheduleOnRN } from "react-native-worklets";

/**
 * The splash and loading screen, drawn with Skia and driven by Reanimated.
 *
 * A sunny Hạ Long sky with a turning Đông Sơn sun, drifting clouds and a
 * rolling sea; Little Giant hops on a tiny island under the rainbow title.
 * When the game is ready the scene opens like a Mario 64 iris, a circle
 * growing from the mascot to reveal the game underneath. For a level change
 * it closes the same way, and opens again once the new level is on screen.
 */

const LIME = "#d5f64b";
const FOREST = "#234d37";
const GOLD = "#f2c33d";
const RAINBOW = ["#ff5a4e", "#ffb03a", "#ffe14d", "#7ed957", "#4fc3f7", "#8f7cf7", "#ff6fb1"];

type Props = {
  /** true: the curtain is (or closes to) fully drawn; false: it irises open. */
  covered: boolean;
  /** 0..1 while the engine boots; drives the lime bar. */
  progress: SharedValue<number>;
  /** the line under the bar: a tip, or where the boat is sailing */
  caption: string;
};

export function Curtain({ covered, progress, caption }: Props) {
  const { width: W, height: H } = useWindowDimensions();
  const [mounted, setMounted] = useState(true);
  const maxR = Math.hypot(W, H);
  // radius of the see-through hole: 0 = fully covered, maxR = fully open
  const hole = useSharedValue(0);

  useEffect(() => {
    if (covered) {
      setMounted(true);
      hole.value = withTiming(0, { duration: 520, easing: Easing.in(Easing.cubic) });
    } else {
      hole.value = withDelay(
        200,
        withTiming(maxR, { duration: 950, easing: Easing.in(Easing.quad) }, (done) => {
          if (done) scheduleOnRN(setMounted, false);
        }),
      );
    }
  }, [covered, hole, maxR]);

  if (!mounted) return null;
  return (
    <Canvas style={StyleSheet.absoluteFill} pointerEvents={covered ? "auto" : "none"}>
      <Scene W={W} H={H} hole={hole} progress={progress} caption={caption} />
    </Canvas>
  );
}

function Scene({
  W,
  H,
  hole,
  progress,
  caption,
}: {
  W: number;
  H: number;
  hole: SharedValue<number>;
  progress: SharedValue<number>;
  caption: string;
}) {
  const clock = useClock();
  const hero = useImage(require("../assets/hero.png"));
  const unit = Math.min(W, H); // everything scales with the short side
  const titleFont = useFont(require("../assets/fonts/Baloo2-ExtraBold.ttf"), unit * 0.16);
  const subFont = useFont(require("../assets/fonts/Baloo2-ExtraBold.ttf"), unit * 0.085);
  const bodyFont = useFont(require("../assets/fonts/Nunito-Bold.ttf"), unit * 0.042);

  // where things sit
  const heroSize = unit * 0.3;
  const islandY = H * 0.74;
  const heroX = W * 0.5;
  const irisY = islandY - heroSize * 0.45;

  const iris = useDerivedValue(() => {
    const p = Skia.Path.Make();
    p.addCircle(heroX, irisY, hole.value);
    return p;
  });
  const rimR = useDerivedValue(() => hole.value);
  const rimOpacity = useDerivedValue(() => (hole.value > 1 ? 1 : 0));

  return (
    <Group>
      <Group clip={iris} invertClip>
        <Sky W={W} H={H} />
        <Sun cx={W * 0.5} cy={H * 0.38} r={unit * 0.62} clock={clock} />
        <Clouds W={W} H={H} unit={unit} clock={clock} />
        <Sea W={W} H={H} clock={clock} />
        <Island cx={heroX} cy={islandY} unit={unit} />
        {hero && <Hero image={hero} cx={heroX} groundY={islandY} size={heroSize} clock={clock} />}
        {titleFont && subFont && (
          <Title W={W} y={H * 0.2} font={titleFont} subFont={subFont} clock={clock} />
        )}
        <Sparkles W={W} H={H} unit={unit} clock={clock} />
        {bodyFont && (
          <Loader W={W} H={H} unit={unit} font={bodyFont} progress={progress} caption={caption} />
        )}
      </Group>
      {/* a lime rim on the opening iris */}
      <Circle cx={heroX} cy={irisY} r={rimR} style="stroke" strokeWidth={unit * 0.018} color={LIME} opacity={rimOpacity} />
    </Group>
  );
}

function Sky({ W, H }: { W: number; H: number }) {
  return (
    <Fill>
      <LinearGradient
        start={vec(0, 0)}
        end={vec(0, H)}
        colors={["#5fb4ee", "#9fd6f7", "#e9f6ff", "#fff3cf"]}
        positions={[0, 0.45, 0.72, 1]}
      />
    </Fill>
  );
}

/** The Đông Sơn drum sun: rings and 14 rays turning slowly behind the title. */
function Sun({ cx, cy, r, clock }: { cx: number; cy: number; r: number; clock: SharedValue<number> }) {
  const rays = useMemo(() => {
    const p = Skia.Path.Make();
    const n = 14;
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2;
      const w = (Math.PI / n) * 0.42;
      p.moveTo(cx + Math.cos(a - w) * r * 0.2, cy + Math.sin(a - w) * r * 0.2);
      p.lineTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r);
      p.lineTo(cx + Math.cos(a + w) * r * 0.2, cy + Math.sin(a + w) * r * 0.2);
      p.close();
    }
    return p;
  }, [cx, cy, r]);
  const transform = useDerivedValue(() => [{ rotate: (clock.value / 1000) * 0.12 }]);
  return (
    <Group origin={vec(cx, cy)} transform={transform}>
      <Path path={rays} color="rgba(255,255,255,0.22)" />
      <Circle cx={cx} cy={cy} r={r * 0.2} color="rgba(255,255,255,0.18)" />
      <Circle cx={cx} cy={cy} r={r * 0.28} style="stroke" strokeWidth={r * 0.012} color="rgba(255,255,255,0.28)" />
      <Circle cx={cx} cy={cy} r={r * 0.36} style="stroke" strokeWidth={r * 0.008} color="rgba(255,255,255,0.2)" />
    </Group>
  );
}

function cloudPath(x: number, y: number, s: number) {
  const p = Skia.Path.Make();
  p.addCircle(x, y, s * 0.5);
  p.addCircle(x + s * 0.55, y - s * 0.22, s * 0.62);
  p.addCircle(x + s * 1.15, y, s * 0.48);
  p.addRRect(Skia.RRectXY(Skia.XYWHRect(x - s * 0.3, y - s * 0.05, s * 1.8, s * 0.52), s * 0.26, s * 0.26));
  return p;
}

function Cloud({ W, y, s, speed, offset, clock }: { W: number; y: number; s: number; speed: number; offset: number; clock: SharedValue<number> }) {
  const path = useMemo(() => cloudPath(0, 0, s), [s]);
  const span = W + s * 3;
  const transform = useDerivedValue(() => [
    { translateX: ((clock.value / 1000) * speed + offset) % span - s * 1.8 },
    { translateY: y },
  ]);
  return (
    <Group transform={transform}>
      <Path path={path} color="rgba(40,90,140,0.12)" transform={[{ translateY: s * 0.12 }]} />
      <Path path={path} color="white" />
    </Group>
  );
}

function Clouds({ W, H, unit, clock }: { W: number; H: number; unit: number; clock: SharedValue<number> }) {
  return (
    <Group>
      <Cloud W={W} y={H * 0.12} s={unit * 0.16} speed={unit * 0.05} offset={W * 0.1} clock={clock} />
      <Cloud W={W} y={H * 0.3} s={unit * 0.11} speed={unit * 0.035} offset={W * 0.7} clock={clock} />
      <Cloud W={W} y={H * 0.08} s={unit * 0.09} speed={unit * 0.028} offset={W * 1.2} clock={clock} />
    </Group>
  );
}

/** The bay along the bottom: a band of sea whose top edge rolls, with a foam line. */
function Sea({ W, H, clock }: { W: number; H: number; clock: SharedValue<number> }) {
  const top = H * 0.8;
  const wave = useDerivedValue(() => {
    const t = clock.value / 1000;
    const p = Skia.Path.Make();
    p.moveTo(0, H);
    const steps = 48;
    for (let i = 0; i <= steps; i++) {
      const x = (i / steps) * W;
      p.lineTo(x, top + Math.sin(x * 0.018 + t * 1.6) * 5 + Math.sin(x * 0.041 - t * 2.3) * 3);
    }
    p.lineTo(W, H);
    p.close();
    return p;
  });
  return (
    <Group>
      <Path path={wave}>
        <LinearGradient start={vec(0, top)} end={vec(0, H)} colors={["#58c3f0", "#2f93d6"]} />
      </Path>
      <Path path={wave} style="stroke" strokeWidth={4} color="rgba(255,255,255,0.85)" />
    </Group>
  );
}

function Island({ cx, cy, unit }: { cx: number; cy: number; unit: number }) {
  const w = unit * 0.5;
  return (
    <Group>
      <Oval x={cx - w * 0.5} y={cy - unit * 0.02} width={w} height={unit * 0.14} color="#d9b47a" />
      <Oval x={cx - w * 0.5} y={cy - unit * 0.055} width={w} height={unit * 0.12} color="#5fbf45" />
      <Oval x={cx - w * 0.49} y={cy - unit * 0.06} width={w * 0.98} height={unit * 0.105} color="#7ed957" />
      <Oval x={cx - w * 0.3} y={cy - unit * 0.052} width={w * 0.34} height={unit * 0.03} color="rgba(255,255,255,0.28)" />
    </Group>
  );
}

/** Little Giant hopping in place: a stretch on the way up, a squash on landing. */
function Hero({
  image,
  cx,
  groundY,
  size,
  clock,
}: {
  image: ReturnType<typeof useImage> & object;
  cx: number;
  groundY: number;
  size: number;
  clock: SharedValue<number>;
}) {
  const hopTransform = useDerivedValue(() => {
    const t = (clock.value / 1000) * 1.7; // hops per second
    const ph = t - Math.floor(t);
    const air = Math.sin(ph * Math.PI); // 0 on the ground, 1 at the top
    const land = ph < 0.12 ? 1 - ph / 0.12 : 0; // squash just after touching down
    const sy = 1 + air * 0.06 - land * 0.12;
    const sx = 1 - air * 0.04 + land * 0.1;
    return [{ translateY: -air * size * 0.2 }, { scaleX: sx }, { scaleY: sy }];
  });
  const shadow = useDerivedValue(() => {
    const t = (clock.value / 1000) * 1.7;
    const air = Math.sin((t - Math.floor(t)) * Math.PI);
    return 1 - air * 0.45;
  });
  const shadowTransform = useDerivedValue(() => [{ scale: shadow.value }]);
  return (
    <Group>
      <Group origin={vec(cx, groundY - size * 0.04)} transform={shadowTransform}>
        <Oval x={cx - size * 0.3} y={groundY - size * 0.07} width={size * 0.6} height={size * 0.1} color="rgba(20,60,30,0.3)" />
      </Group>
      <Group origin={vec(cx, groundY)} transform={hopTransform}>
        <SkiaImage image={image} x={cx - size / 2} y={groundY - size * 0.9} width={size} height={size} fit="contain" />
      </Group>
    </Group>
  );
}

function Letter({
  ch,
  x,
  y,
  i,
  font,
  color,
  outline,
  clock,
  amp,
}: {
  ch: string;
  x: number;
  y: number;
  i: number;
  font: SkFont;
  color: string;
  outline: number;
  clock: SharedValue<number>;
  amp: number;
}) {
  const transform = useDerivedValue(() => [
    { translateY: Math.sin((clock.value / 1000) * 5 - i * 0.55) * amp },
  ]);
  return (
    <Group transform={transform}>
      <SkiaText x={x} y={y + outline * 0.9} text={ch} font={font} color="rgba(10,30,70,0.35)" style="stroke" strokeWidth={outline} strokeJoin="round" />
      <SkiaText x={x} y={y} text={ch} font={font} color="white" style="stroke" strokeWidth={outline} strokeJoin="round" />
      <SkiaText x={x} y={y} text={ch} font={font} color={color} />
    </Group>
  );
}

/** A rainbow word, letter by letter, the same way the game's own title draws it. */
function Word({
  text,
  W,
  y,
  font,
  clock,
  gold,
  phase,
}: {
  text: string;
  W: number;
  y: number;
  font: SkFont;
  clock: SharedValue<number>;
  gold?: boolean;
  phase: number;
}) {
  const size = font.getSize();
  const letters = useMemo(() => {
    const out: { ch: string; x: number; color: string }[] = [];
    const tight = -size * 0.04;
    const widths = [...text].map((ch) => (ch === " " ? size * 0.28 : font.measureText(ch).width));
    const total = widths.reduce((a, b) => a + b + tight, -tight);
    let x = (W - total) / 2;
    let k = 0;
    [...text].forEach((ch, i) => {
      out.push({ ch, x, color: gold ? GOLD : RAINBOW[k % RAINBOW.length] });
      x += widths[i] + tight;
      if (ch !== " ") k++;
    });
    return out;
  }, [text, W, font, size, gold]);
  return (
    <Group>
      {letters.map((l, i) =>
        l.ch === " " ? null : (
          <Letter key={i} ch={l.ch} x={l.x} y={y} i={i + phase} font={font} color={l.color} outline={size * 0.16} clock={clock} amp={size * 0.05} />
        ),
      )}
    </Group>
  );
}

function Title({ W, y, font, subFont, clock }: { W: number; y: number; font: SkFont; subFont: SkFont; clock: SharedValue<number> }) {
  // the title drops in with a little overshoot
  const intro = useSharedValue(0);
  useEffect(() => {
    intro.value = withTiming(1, { duration: 700, easing: Easing.out(Easing.back(2)) });
  }, [intro]);
  const transform = useDerivedValue(() => [
    { translateY: (1 - intro.value) * -y },
    { scale: 0.7 + intro.value * 0.3 },
  ]);
  return (
    <Group origin={vec(W / 2, y)} transform={transform}>
      <Word text="LITTLE GIANT" W={W} y={y} font={font} clock={clock} phase={0} />
      <Word text="STAR HOP" W={W} y={y + subFont.getSize() * 1.15} font={subFont} clock={clock} gold phase={4} />
      <GoldStars W={W} y={y + subFont.getSize() * 0.78} font={subFont} clock={clock} />
    </Group>
  );
}

/** A spinning gold star either side of STAR HOP (the font has no ★ glyph). */
function GoldStars({ W, y, font, clock }: { W: number; y: number; font: SkFont; clock: SharedValue<number> }) {
  const size = font.getSize();
  const half = [..."STAR HOP"].reduce((a, ch) => a + (ch === " " ? size * 0.28 : font.measureText(ch).width) - size * 0.04, 0) / 2;
  const r = size * 0.42;
  const star = useMemo(() => {
    const p = Skia.Path.Make();
    for (let i = 0; i < 10; i++) {
      const a = -Math.PI / 2 + (i * Math.PI) / 5;
      const rr = i % 2 === 0 ? r : r * 0.45;
      if (i === 0) p.moveTo(Math.cos(a) * rr, Math.sin(a) * rr);
      else p.lineTo(Math.cos(a) * rr, Math.sin(a) * rr);
    }
    p.close();
    return p;
  }, [r]);
  const spin = useDerivedValue(() => Math.sin((clock.value / 1000) * 2.2) * 0.35);
  const left = useDerivedValue(() => [{ translateX: W / 2 - half - r * 1.6 }, { translateY: y - r * 0.2 }, { rotate: spin.value }]);
  const right = useDerivedValue(() => [{ translateX: W / 2 + half + r * 1.6 }, { translateY: y - r * 0.2 }, { rotate: -spin.value }]);
  return (
    <Group>
      {[left, right].map((t, i) => (
        <Group key={i} transform={t}>
          <Path path={star} color="white" style="stroke" strokeWidth={size * 0.16} strokeJoin="round" />
          <Path path={star} color={GOLD} />
        </Group>
      ))}
    </Group>
  );
}

/** Four-point twinkles scattered round the title. */
function Sparkles({ W, H, unit, clock }: { W: number; H: number; unit: number; clock: SharedValue<number> }) {
  const spots = useMemo(
    () => [
      [0.2, 0.16, 0.0],
      [0.8, 0.2, 0.35],
      [0.27, 0.42, 0.7],
      [0.74, 0.46, 0.15],
      [0.12, 0.6, 0.55],
      [0.9, 0.62, 0.85],
    ],
    [],
  );
  return (
    <Group>
      {spots.map(([x, y, off], i) => (
        <Twinkle key={i} cx={W * x} cy={H * y} s={unit * 0.03} off={off} clock={clock} />
      ))}
    </Group>
  );
}

function Twinkle({ cx, cy, s, off, clock }: { cx: number; cy: number; s: number; off: number; clock: SharedValue<number> }) {
  const star = useMemo(() => {
    const p = Skia.Path.Make();
    p.moveTo(cx, cy - s);
    p.quadTo(cx, cy, cx + s, cy);
    p.quadTo(cx, cy, cx, cy + s);
    p.quadTo(cx, cy, cx - s, cy);
    p.quadTo(cx, cy, cx, cy - s);
    p.close();
    return p;
  }, [cx, cy, s]);
  const transform = useDerivedValue(() => {
    const k = Math.max(0, Math.sin(((clock.value / 1000) * 0.9 + off) * Math.PI * 2));
    return [{ scale: 0.2 + k * 0.8 }];
  });
  const opacity = useDerivedValue(() => Math.max(0, Math.sin(((clock.value / 1000) * 0.9 + off) * Math.PI * 2)));
  return (
    <Group origin={vec(cx, cy)} transform={transform} opacity={opacity}>
      <Path path={star} color="white" />
    </Group>
  );
}

/** The loading bar (a lime pill) and a caption under it. */
function Loader({
  W,
  H,
  unit,
  font,
  progress,
  caption,
}: {
  W: number;
  H: number;
  unit: number;
  font: SkFont;
  progress: SharedValue<number>;
  caption: string;
}) {
  const bw = Math.min(W * 0.36, unit * 0.9);
  const bh = unit * 0.034;
  const x = (W - bw) / 2;
  const y = H * 0.85;
  const fillW = useDerivedValue(() => Math.max(bh, bw * Math.min(1, progress.value)));
  const tw = font.measureText(caption).width;
  return (
    <Group>
      <RoundedRect x={x - 3} y={y - 3} width={bw + 6} height={bh + 6} r={(bh + 6) / 2} color="rgba(16,40,28,0.55)" />
      <RoundedRect x={x} y={y} width={fillW} height={bh} r={bh / 2} color={LIME} />
      <SkiaText x={(W - tw) / 2} y={y + bh + font.getSize() * 1.45} text={caption} font={font} color={FOREST} style="stroke" strokeWidth={font.getSize() * 0.28} strokeJoin="round" />
      <SkiaText x={(W - tw) / 2} y={y + bh + font.getSize() * 1.45} text={caption} font={font} color="white" />
    </Group>
  );
}
