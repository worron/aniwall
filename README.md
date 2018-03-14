## Aniwall

Simple GUI application for creating custom colored minimalist wallpapers from image patterns.

#### Screenshots
<p align="center"><img src="http://i.imgur.com/ceRbAXh.png"></p>
<p align="center"><a href="https://youtu.be/OoHnJsiGe-Y">Video Demo</a></p>

#### Dependencies
* GTK+ >= 3.18
* Python >= 3.5
* python gobject introspection
* python lxml

It's also required glib2 `glib-compile-resources` and `glib-compile-schemas` binary for compiling resources.

#### Installation and Usage
Install
```shell
$ git clone https://github.com/worron/aniwall.git ~/aniwall
$ python3 ~/aniwall/setup.py install
```
Image patterns distributed separately from application. Using `--recursive` with git clone command you can automatically download base images pack to the same folder, otherwise get the images from `wallpapers` submodule in any other  way. Anyway, you should set images location in application preferences on first launch.

As application mostly written with python it can be launched without installation, but glib resources should be compiled first
```shell
$ git clone https://github.com/worron/aniwall.git ~/aniwall
$ glib-compile-schemas ~/aniwall/aniwall/data
$ cd ~/aniwall/aniwall/data && glib-compile-resources aniwall.gresource.xml
$ python3 ~/aniwall/aniwall/run.py
```
#### Image Pattern Format
Aniwall use SVG images with tagged in a special way elements. Follow tag id naming scheme user can easily create his own image patterns. Here is image pattern example
```svg
<svg height="1080" width="1920" xmlns="http://www.w3.org/2000/svg">
  <path id="background" d="m0 0v1080h1920v-1080z" fill="#202020"/>
  <g id="transform" transform="translate(0,0) scale(1.00)">
    <path id="color1" d="m260.791 102.853v360h640v-360z" fill="#a00000"/>
    <path id="color2" d="m1019.22 102.853v360h639.99v-360z" fill="#00a000"/>
    <path id="color3" d="m260.793 561.867v360h639.995v-360z" fill="#0000a0"/>
    <path id="color4" d="m1019.21 561.867v360h640v-360z" fill="#a000a0"/>
  </g>
</svg>
```

Certain attributes of that structure can be changed using application GUI.

tag id        | customizable attribute
------------ | -------------
transform     | transform*
background    | fill
colorN        | fill

\* Work only with given mask `translate(X,X) scale(X.XX)`
