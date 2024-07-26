import scrapy


class PriceOyeSpider(scrapy.Spider):
    name = "priceoye_scraper"
    allowed_domains = ["priceoye.pk"]
    start_urls = ['https://priceoye.pk/']

    def parse(self, response):
        categories = response.css('a.categoryCard::attr(href)').getall()

        for category_url in categories:
            yield scrapy.Request(url=category_url, callback=self.parse_product_category)

    def parse_product_category(self, response):
        products = response.css('div.productBox.b-productBox')

        for product in products:
            product_title = product.css('div.p-title.bold.h5::text').get(default='N/A').strip()
            price_elements = product.css('div.price-box.p1::text').getall()
            price = ''.join(price_elements).strip()
            discount = product.css('div.price-diff-saving::text').get(default='N/A').strip()
            image_url = product.css('amp-img::attr(src)').get(default='N/A')
            product_url = response.urljoin(product.css('a::attr(href)').get(default='N/A'))

            yield response.follow(
                product_url,
                self.parse_product_details,
                meta={
                    'product_title': product_title,
                    'price': price,
                    'discount': discount,
                    'image_url': image_url
                }
            )

        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            next_page_url = response.urljoin(next_page)
            yield scrapy.Request(next_page_url, callback=self.parse_product_category)

    def parse_product_details(self, response):
        product_title = response.meta['product_title']
        price = response.meta['price']
        discount = response.meta['discount']
        image_url = response.meta['image_url']

        product_specifications = self.extract_product_specifications(response)

        yield {
            'product_title': product_title,
            'price': price,
            'discount': discount,
            'image_url': image_url,
            'specifications': product_specifications
        }

    def extract_product_specifications(self, response):
        product_specifications = {}
        specification_sections = response.css('div.product-spec-section table.p-spec-table.card')

        for section in specification_sections:
            specification_category_title = section.css('thead th::text').get(default='N/A').strip()
            product_specifications[specification_category_title] = {}

            specification_rows = section.css('tbody tr')
            for specification_row in specification_rows:
                key = specification_row.css('th::text').get(default='N/A').strip()
                value = specification_row.css('td::text').get(default='N/A').strip()
                product_specifications[specification_category_title][key] = value

        return product_specifications
