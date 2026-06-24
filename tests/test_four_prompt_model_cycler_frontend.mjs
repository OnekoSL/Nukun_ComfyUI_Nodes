import assert from "node:assert/strict";

import {
    MAX_RANDOM_SEED,
    createRandomSeedState,
    enterSeedGroup,
    lockSeedControl,
    randomSeed,
} from "../web/four_prompt_model_cycler_core.mjs";

const state = createRandomSeedState();
assert.equal(enterSeedGroup(state, "random", 0), true);
assert.equal(enterSeedGroup(state, "random", 1), false);
assert.equal(enterSeedGroup(state, "random", 2), false);
assert.equal(enterSeedGroup(state, "random", 3), false);
assert.equal(enterSeedGroup(state, "random", 4), true);
assert.equal(enterSeedGroup(state, "random", 7), false);
assert.equal(enterSeedGroup(state, "random", 8), true);

let controlledSeed = 12345;
const savedRandomControl = {
    value: "randomize",
    beforeQueued() {
        if (this.value === "randomize") {
            controlledSeed = 99999;
        }
    },
};
assert.equal(lockSeedControl(savedRandomControl), true);
assert.equal(savedRandomControl.value, "fixed");
savedRandomControl.value = "randomize";
savedRandomControl.beforeQueued();
assert.equal(savedRandomControl.value, "fixed");
assert.equal(controlledSeed, 12345);

assert.equal(enterSeedGroup(state, "fixed", 8), false);
assert.equal(enterSeedGroup(state, "random", 8), true);

for (let index = 0; index < 20; index += 1) {
    const value = randomSeed();
    assert.equal(Number.isSafeInteger(value), true);
    assert.equal(value >= 0 && value <= MAX_RANDOM_SEED, true);
}

console.log("four_prompt_model_cycler frontend tests: ok");
