import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const TARGET_NODE = "NukunVocabMultiStringList";
const TARGET_DISPLAY_NAME = "Multi Vocab String List (Nukun)";
const RANDOM_LABEL = "(random)";
const SLOT_COUNT = 4;
const WORD_COUNT = 3;
const vocabCache = new Map();
const configuredNodes = new WeakSet();

function widget(node, name) {
    return node.widgets?.find((candidate) => candidate?.name === name);
}

async function loadWords(vocabFile) {
    if (!vocabFile) {
        return [];
    }

    if (vocabCache.has(vocabFile)) {
        return vocabCache.get(vocabFile);
    }

    const response = await api.fetchApi(`/nukun/vocab/words?file=${encodeURIComponent(vocabFile)}`, {
        cache: "no-store",
    });
    if (!response.ok) {
        throw new Error(`Failed to load vocabulary: ${vocabFile}`);
    }

    const payload = await response.json();
    const words = Array.isArray(payload.words) ? payload.words : [];
    vocabCache.set(vocabFile, words);
    return words;
}

function configureWordWidget(wordWidget) {
    if (!wordWidget) {
        return;
    }

    wordWidget.type = "combo";
    wordWidget.options = wordWidget.options || {};
    wordWidget.options.values = wordWidget.options.values || [RANDOM_LABEL];
    if (!wordWidget.value) {
        wordWidget.value = RANDOM_LABEL;
    }
}

function updateWordWidget(wordWidget, words) {
    if (!wordWidget) {
        return;
    }

    const values = [RANDOM_LABEL, ...words];
    wordWidget.type = "combo";
    wordWidget.options = wordWidget.options || {};
    wordWidget.options.values = values;

    if (!values.includes(wordWidget.value)) {
        wordWidget.value = RANDOM_LABEL;
    }
}

async function updateSlotWords(node, slot) {
    const vocabWidget = widget(node, `vocab_file_${slot}`);
    const vocabFile = vocabWidget?.value;
    let words = [];

    try {
        words = await loadWords(vocabFile);
    } catch (error) {
        console.warn(`[Nukun] ${error.message}`);
    }

    for (let wordIndex = 1; wordIndex <= WORD_COUNT; wordIndex += 1) {
        updateWordWidget(widget(node, `word_${slot}_${wordIndex}`), words);
    }

    app.graph?.setDirtyCanvas?.(true, true);
}

function setupNode(node) {
    node.serialize_widgets = true;

    for (let slot = 1; slot <= SLOT_COUNT; slot += 1) {
        for (let wordIndex = 1; wordIndex <= WORD_COUNT; wordIndex += 1) {
            configureWordWidget(widget(node, `word_${slot}_${wordIndex}`));
        }

        const vocabWidget = widget(node, `vocab_file_${slot}`);
        if (vocabWidget) {
            const previousCallback = vocabWidget.callback;
            vocabWidget.callback = function (value, ...args) {
                const result = previousCallback?.call(this, value, ...args);
                updateSlotWords(node, slot);
                return result;
            };
        }

        updateSlotWords(node, slot);
    }
}

function isTargetNode(nodeType, nodeData) {
    return (
        nodeData?.name === TARGET_NODE ||
        nodeData?.name === TARGET_DISPLAY_NAME ||
        nodeType?.comfyClass === TARGET_NODE ||
        nodeType?.title === TARGET_DISPLAY_NAME
    );
}

function isTargetNodeInstance(node) {
    return (
        node?.comfyClass === TARGET_NODE ||
        node?.comfyClass === TARGET_DISPLAY_NAME ||
        node?.type === TARGET_NODE ||
        node?.type === TARGET_DISPLAY_NAME ||
        node?.title === TARGET_DISPLAY_NAME
    );
}

function setupTargetNode(node) {
    if (!node || configuredNodes.has(node)) {
        return;
    }

    configuredNodes.add(node);
    setupNode(node);
}

app.registerExtension({
    name: "Nukun.VocabMultiSelect",
    nodeCreated(node) {
        if (isTargetNodeInstance(node)) {
            setupTargetNode(node);
        }
    },
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!isTargetNode(nodeType, nodeData)) {
            return;
        }

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);
            setupTargetNode(this);
            return result;
        };
    },
});
