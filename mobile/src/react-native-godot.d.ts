// @borndotcom/react-native-godot ships without its .d.ts files; these are the parts the app uses.
declare module "@borndotcom/react-native-godot" {
  import type { HostComponent, ViewProps } from "react-native";

  export interface GodotModule {
    createInstance(args: string[]): unknown;
    getInstance(): unknown;
    /** The Godot API root (Engine, classes, singletons). Loosely typed: it mirrors Godot's API. */
    API(): any;
    pause(): void;
    resume(): void;
    is_paused(): boolean;
    destroyInstance(): void;
  }

  export const RTNGodot: GodotModule;
  export function runOnGodotThread<T>(f: () => T): Promise<T>;
  export const RTNGodotView: HostComponent<ViewProps & { windowName?: string }>;
}
