from setuptools import setup, find_packages

setup(
    name="vnpy_akshare_adapter",
    version="1.0.0",
    author="wade1010",
    author_email="640297@qq.com", 
    license="MIT",
    url="https://github.com/wade1010/vnpy_akshare",
    description="AKShare数据服务接口 - VeighNa框架的数据接口适配",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "vnpy>=4.0.0",
        "akshare>=1.16.98"
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent", 
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.10",
    keywords=["vnpy", "quant", "akshare", "trading", "investment"]
)
