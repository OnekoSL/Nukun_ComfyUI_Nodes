export const MAX_RANDOM_SEED = 1125899906842623;
const lockedSeedControls = new WeakSet();

export function randomSeed() {
    if (globalThis.crypto?.getRandomValues) {
        const words = new Uint32Array(2);
        globalThis.crypto.getRandomValues(words);
        const high18Bits = words[0] & 0x3ffff;
        return high18Bits * 0x100000000 + words[1];
    }
    return Math.floor(Math.random() * (MAX_RANDOM_SEED + 1));
}

export function createRandomSeedState() {
    return { lastRandomGroup: null, lastMode: null };
}

export function enterSeedGroup(state, mode, cycleIndex) {
    if (mode !== "random") {
        state.lastRandomGroup = null;
        state.lastMode = mode;
        return false;
    }

    const safeCycleIndex = Math.max(0, Number(cycleIndex) || 0);
    const modelGroup = Math.floor(safeCycleIndex / 4);
    const shouldRandomize = state.lastMode !== "random" || state.lastRandomGroup !== modelGroup;
    state.lastRandomGroup = modelGroup;
    state.lastMode = mode;
    return shouldRandomize;
}

export function lockSeedControl(seedControl) {
    if (!seedControl) {
        return false;
    }

    seedControl.value = "fixed";
    if (lockedSeedControls.has(seedControl)) {
        return true;
    }

    const originalBeforeQueued = seedControl.beforeQueued;
    seedControl.beforeQueued = function (context) {
        this.value = "fixed";
        return originalBeforeQueued?.call(this, context);
    };
    lockedSeedControls.add(seedControl);
    return true;
}
