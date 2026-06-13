import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const TARGET_NODE = "NukunOllamaPromptRefiner";
const TARGET_DISPLAY_NAME = "Ollama Prompt Refiner (Nukun)";
const DEFAULT_MODEL = "autoren-darkidol-llama-3-1-8b:latest";
const configuredNodes = new WeakSet();
const modelCache = new Map();

function widget(node, name) {
    return node.widgets?.find((candidate) => candidate?.name === name);
}

async function loadModels(ollamaUrl) {
    const cacheKey = String(ollamaUrl || "").trim();
    if (modelCache.has(cacheKey)) {
        return modelCache.get(cacheKey);
    }

    const response = await api.fetchApi(`/nukun/ollama/models?url=${encodeURIComponent(cacheKey)}`, {
        cache: "no-store",
    });
    if (!response.ok) {
        throw new Error(`Failed to load Ollama models from ${cacheKey || "default URL"}`);
    }

    const payload = await response.json();
    const models = Array.isArray(payload.models) && payload.models.length ? payload.models : [payload.fallback || DEFAULT_MODEL];
    modelCache.set(cacheKey, models);
    return models;
}

function updateModelWidget(modelWidget, models) {
    if (!modelWidget) {
        return;
    }

    modelWidget.type = "combo";
    modelWidget.options = modelWidget.options || {};
    modelWidget.options.values = models;

    if (!models.includes(modelWidget.value)) {
        modelWidget.value = models[0] || DEFAULT_MODEL;
    }
}

async function refreshModels(node) {
    const urlWidget = widget(node, "ollama_url");
    const modelWidget = widget(node, "ollama_model");
    if (!modelWidget) {
        return;
    }

    let models = [modelWidget.value || DEFAULT_MODEL];
    try {
        models = await loadModels(urlWidget?.value);
    } catch (error) {
        console.warn(`[Nukun] ${error.message}`);
    }

    updateModelWidget(modelWidget, models);
    app.graph?.setDirtyCanvas?.(true, true);
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

function setupNode(node) {
    if (!node || configuredNodes.has(node)) {
        return;
    }

    configuredNodes.add(node);
    node.serialize_widgets = true;

    const urlWidget = widget(node, "ollama_url");
    if (urlWidget) {
        const previousCallback = urlWidget.callback;
        urlWidget.callback = function (value, ...args) {
            const result = previousCallback?.call(this, value, ...args);
            refreshModels(node);
            return result;
        };
    }

    refreshModels(node);
}

app.registerExtension({
    name: "Nukun.OllamaModelSelect",
    nodeCreated(node) {
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
