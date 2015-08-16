from DomainFinderSrc.PageNavigator import NavEleType, SelecElement


class BulkCheckElements:
    id_domains_input_field = 1
    id_search_button = 2
    id_check_out_button = 9
    id_contiune_button = 10
    class_cart_products = 3
    class_product = 4
    class_domain_name = 5
    class_amount = 11
    class_price_plan = 12
    class_msg = 6
    msg_domain_avaiable = 7
    msg_domain_bad = 8


    @staticmethod
    def get_element_by_id(id: int)->SelecElement:
        return {
            BulkCheckElements.id_domains_input_field: SelecElement('bulkSearchArea'),  # you can put maximum of 500 domains into it
            BulkCheckElements.id_search_button: SelecElement('bulkSearchBtn'),  # press this to perform search, then if check class_cart_products exist
            BulkCheckElements.id_check_out_button: SelecElement('bulkProceedtoCheckout'), # find this element to ensure the result page is loaded, opt 1
            BulkCheckElements.id_contiune_button: SelecElement('btn-dpp-products'), # same as above, but it can popup instead of above, so check it as well, opt2

        }.get(id)

    @staticmethod  # use this with css selector, once you know the class path
    def get_element_by_class(class_path: int)->SelecElement:
        return {
            BulkCheckElements.class_cart_products: SelecElement('cart-products', NavEleType.IsClass),
            BulkCheckElements.class_product: SelecElement('product', NavEleType.IsClass),  # get the product item, then call class 'name' and 'message'
            BulkCheckElements.class_domain_name: SelecElement('name', NavEleType.IsClass),  # contains the domain name
            BulkCheckElements.class_amount: SelecElement('amount', NavEleType.IsClass),  # contains the price info
            BulkCheckElements.class_price_plan:SelecElement('cart-simple-selector-list', NavEleType.IsClass), # contains a <li> of price plans, default is 2 years
            BulkCheckElements.class_msg: SelecElement('message', NavEleType.IsClass),  # check message with get_return_msg
        }.get(class_path)

    @staticmethod
    def get_return_msg(msg_type: int):
        return {
            BulkCheckElements.msg_domain_avaiable: 'Matching Domains Available',
            BulkCheckElements.msg_domain_bad: 'bad'
        }.get(msg_type)
