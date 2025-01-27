# How to run
```
python3 start.py <app path> -s <device serail> -d <exploration depth> -o <output file path> -t <timeout>
```
  -s SERIAL, --serial SERIAL
                        specify the device serial for exploration
                        
  -d DEPTH, --depth DEPTH
                        specify the depth of exploration, default is 2
                        
  -o OUTPUT, --output OUTPUT
                        specify the output file path of hstg
                        
  -t TIMEOUT, --timeout TIMEOUT
                        specify the timeout of exploration

```
python3 start.py --source_device=<source device serail> --target_device=<target device serail> --source_app=<source app path>
--target_app=<target app path> --source_hstg=<source hstg path> --target_hstg=<target hstg path> -o <output file path>
```

  --source_device SOURCE_DEVICE
                        specify the source device serial for detection
                        
  --target_device TARGET_DEVICE
                        specify the target device serial for detection
                        
  --source_app SOURCE_APP
                        specify the source app path for detection
                        
  --target_app TARGET_APP
                        specify the target app path for detection
                        
  --source_hstg SOURCE_HSTG
                        specify the source hstg path for detection
                        
  --target_hstg TARGET_HSTG
                        specify the target hstg path for detection
                        
  -o OUTPUT, --output OUTPUT
                        specify the output file path of detection
