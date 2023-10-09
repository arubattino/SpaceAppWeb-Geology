# NASA Space App Challenge 2023 - GEOLOGY

How to use: run app.py and http://127.0.0.1:8050/ in your browser.

If you use Docker, you can build the container I provide with all the necessary requirements and more.

## Docker
#### Container Description: 
Ubuntu 22.04 + GDAL 3.4 + Python 3.9 + Python Libraries


#### 1. Install


- **CPU:**
```bash
$ sudo docker build -t spaceapp -f docker/Dockerfile .
```


### 2. Run 

#### Run Docker with CPU-bash
```bash
$ sudo docker run --rm --name spaceapp --net host -it \
    -v $(pwd):/src \
    --workdir /src \
    spaceapp \
    bash
```

#### Jupyter Lab

jupyter notebook --ip 0.0.0.0 --no-browser --allow-root