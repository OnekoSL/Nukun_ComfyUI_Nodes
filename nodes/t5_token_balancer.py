class T5Balancer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tokenizer": ("CLIP", {"tooltip": "The loaded T5 Tokenizer to use."}),
                "target": (
                    "INT",
                    {
                        "default": 768,
                        "min": 0,
                        "max": 4096,
                        "step": 1,
                        "tooltip": "Minimum number of tokens to balance toward.",
                    },
                ),
                "positive": ("STRING", {"multiline": True, "dynamicPrompts": True}),
                "negative": ("STRING", {"multiline": True, "dynamicPrompts": True}),
            },
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "balance"
    CATEGORY = "Nukun/Conditioning"
    DESCRIPTION = (
        "Encodes positive and negative text prompts using a T5 Tokenizer model. "
        "The positive prompt is extended to the target token length, "
        "and the negative prompt is padded to match the resulting token count."
    )

    def balance(self, tokenizer, target, positive, negative):
        if tokenizer is None:
            raise RuntimeError("ERROR: A valid tokenizer is required.")

        tok = tokenizer.clone()

        tok.set_tokenizer_option("pile_t5xl_min_length", target)
        tokens_p = tok.tokenize(positive)
        token_count_p = len(tokens_p["pile_t5xl"][0])
        cond_p = tok.encode_from_tokens_scheduled(tokens_p)

        tok.set_tokenizer_option("pile_t5xl_min_padding", token_count_p)
        tokens_n = tok.tokenize(negative)
        cond_n = tok.encode_from_tokens_scheduled(tokens_n)

        return (cond_p, cond_n)


NODE_CLASS_MAPPINGS = {
    "T5Balancer": T5Balancer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "T5Balancer": "T5 Token-based Prompt Balancer",
}
