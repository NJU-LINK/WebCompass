from setuptools import setup, find_packages

setup(
    name="webcompass",
    version="1.0.0",
    description="WebCompass: A Benchmark for Evaluating LLMs on Web Generation Tasks",
    author="WebCompass Team",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "openai>=1.0.0",
        "tqdm",
        "Pillow",
    ],
    extras_require={
        "video": ["opencv-python"],
        "dev": ["pytest", "black", "isort"],
    },
    entry_points={
        "console_scripts": [
            "webcompass-text-inference=generation.scripts.run_text_inference:main",
            "webcompass-image-inference=generation.scripts.run_image_inference:main",
            "webcompass-video-inference=generation.scripts.run_video_inference:main",
            "webcompass-text-checklist=generation.scripts.generate_text_checklist:main",
            "webcompass-image-checklist=generation.scripts.generate_image_checklist:main",
            "webcompass-video-checklist=generation.scripts.generate_video_checklist:main",
        ],
    },
)
