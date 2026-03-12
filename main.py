from script.parser_echo import echo_pipeline
from script.parser_livpost import thePost_pipeline
from script.parser_wirralglobe import wirral_pipeline
import time 


if __name__ == "__main__":
    while True:
        echo_pipeline()
        thePost_pipeline()
        wirral_pipeline()
        time.sleep(300)
        print("服務已啟動，每五分鐘將自動執行一次...")  