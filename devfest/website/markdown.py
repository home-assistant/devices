"""Markdown helpers."""

import humanmark


def prefix_images(text, prefix):
    """Prefix all images in a markdown text with a URL."""
    doc = humanmark.loads(text)

    images = doc.find(
        # Only find image nodes
        humanmark.ast.Image,
        # A negative value means to search the entire tree.
        depth=-1,
    )

    for image in images:
        image.url = f"{prefix}{image.url}"

    return humanmark.dumps(doc)
