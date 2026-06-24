import { app } from "../../../scripts/app.js";
import {
    createRandomSeedState,
    enterSeedGroup,
    lockSeedControl,
    randomSeed,
} from "./four_prompt_model_cycler_core.mjs";

const TARGET_NODES = new Set([
    "NukunFourPromptModelCyclerLoader",
    "NukunFourPromptCheckpointCyclerLoader",
]);
const TARGET_DISPLAY_NAMES = new Set([
    "4-Prompt Model Cycler Loader (Nukun)",
    "4-Prompt Checkpoint Cycler Loader (Nukun)",
]);
const configuredNodes = new WeakSet();

function widget(node, name) {
    return node.widgets?.find((candidate) => candidate?.name === name);
}

function seedControlWidget(node, seedWidget) {
    const linkedControl = seedWidget?.linkedWidgets?.find((candidate) =>
        ["control_after_generate", "control_before_generate", "control before generate", "control after generate"].includes(candidate?.name)
    );
    if (linkedControl) {
        return linkedControl;
    }

    const seedIndex = node.widgets?.indexOf(seedWidget) ?? -1;
    if (seedIndex < 0) {
        return null;
    }
    return node.widgets.slice(seedIndex + 1).find((candidate) =>
        ["control_after_generate", "control_before_generate", "control before generate", "control after generate"].includes(candidate?.name)
    ) || null;
}

function enforceFixedSeedControl(node, seedWidget = widget(node, "seed")) {
    const seedControl = seedControlWidget(node, seedWidget);
    if (!lockSeedControl(seedControl)) {
        return;
    }

    if (!seedControl.nukunOriginalType) {
        seedControl.nukunOriginalType = seedControl.type;
        seedControl.nukunOriginalComputeSize = seedControl.computeSize;
    }
    seedControl.type = "nukun-hidden-seed-control";
    seedControl.computeSize = () => [0, -4];
    node.graph?.setDirtyCanvas?.(true, true);
}

function setupNode(node) {
    if (!node) {
        return;
    }

    const cycleWidget = widget(node, "cycle_index");
    const seedWidget = widget(node, "seed");
    const modeWidget = widget(node, "seed_mode");
    if (!cycleWidget || !seedWidget || !modeWidget) {
        return;
    }

    enforceFixedSeedControl(node, seedWidget);
    if (configuredNodes.has(node)) {
        return;
    }

    configuredNodes.add(node);
    const randomState = createRandomSeedState();
    const previousBeforeQueued = modeWidget.beforeQueued;

    modeWidget.beforeQueued = function (context) {
        previousBeforeQueued?.call(this, context);

        const mode = String(modeWidget.value || "increment");
        if (enterSeedGroup(randomState, mode, cycleWidget.value)) {
            seedWidget.value = randomSeed();
            seedWidget.callback?.(seedWidget.value);
            node.graph?.setDirtyCanvas?.(true, true);
        }
    };
}

function isTargetNode(nodeType, nodeData) {
    return (
        TARGET_NODES.has(nodeData?.name) ||
        TARGET_DISPLAY_NAMES.has(nodeData?.name) ||
        TARGET_NODES.has(nodeType?.comfyClass) ||
        TARGET_DISPLAY_NAMES.has(nodeType?.title)
    );
}

function isTargetNodeInstance(node) {
    return (
        TARGET_NODES.has(node?.comfyClass) ||
        TARGET_DISPLAY_NAMES.has(node?.comfyClass) ||
        TARGET_NODES.has(node?.type) ||
        TARGET_DISPLAY_NAMES.has(node?.type) ||
        TARGET_DISPLAY_NAMES.has(node?.title)
    );
}

app.registerExtension({
    name: "Nukun.FourPromptModelCycler",
    nodeCreated(node) {
        if (isTargetNodeInstance(node)) {
            setupNode(node);
        }
    },
    loadedGraphNode(node) {
        if (isTargetNodeInstance(node)) {
            setupNode(node);
        }
    },
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!isTargetNode(nodeType, nodeData)) {
            return;
        }

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);
            setupNode(this);
            return result;
        };
    },
});
