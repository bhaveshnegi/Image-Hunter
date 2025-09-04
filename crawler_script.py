from icrawler.builtin import GoogleImageCrawler

def download_images(keyword, max_num=600, folder="images"):
    google_crawler = GoogleImageCrawler(storage={'root_dir': folder})
    google_crawler.crawl(keyword=keyword, max_num=max_num)

if __name__ == "__main__":
    # 🔹 Change keyword here for your product
    download_images(keyword="Nike shoes", max_num=50, folder="images/nike")
    # Example for multiple products:
    # download_images(keyword="Adidas shoes", max_num=600, folder="images/adidas")
    # download_images(keyword="Puma shoes", max_num=600, folder="images/puma")
