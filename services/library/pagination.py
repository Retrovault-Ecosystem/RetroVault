class Pagination:


    def __init__(self, items, page_size=50):

        self.items = items

        self.page_size = page_size



    def pages(self):

        return (

            len(self.items)
            +
            self.page_size
            -
            1

        ) // self.page_size



    def get_page(self, number):

        start = (

            number
            *
            self.page_size

        )


        end = start + self.page_size


        return self.items[start:end]
