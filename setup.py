from setuptools import setup

setup(
    name="fast-servo",
    version="0.1.0dev",
    author="Jakub Matyas",
    author_email="jakubk.m@gmail.com",
    description="gateware for Fast Servo platform based on MiSoC",
    url="https://github.com/elhep/Fast-Servo-Firmware",
    packages=[
        "fast_servo", 
        "fast_servo.gateware", 
        "fast_servo.gateware.cores"
    ],
    python_requires=">=3.8",
    include_package_data=True,
)