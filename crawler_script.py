from icrawler.builtin import GoogleImageCrawler

crawler = GoogleImageCrawler(storage={'root_dir': '0-images'})
crawler.crawl(keyword='0', max_num=1000)
