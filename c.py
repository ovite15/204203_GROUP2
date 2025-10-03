def build_prompt(theme: str) -> str:
    return (f"Write a one-sentence uplifting fortune about {theme}."
            if theme.strip() else "Write a one-sentence uplifting fortune.")
