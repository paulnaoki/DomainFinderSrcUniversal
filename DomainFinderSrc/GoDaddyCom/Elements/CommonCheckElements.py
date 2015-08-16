from DomainFinderSrc.PageNavigator import NavEleType, SelecElement


class CommonCheckElement:
    id_domains_input_field = 1
    id_domains_input_again_field = 9
    id_search_again_btn = 4
    css_product_list = 6
    css_search_button = 2
    css_not_available_target = 3
    css_available_target = 5

    class_product_name = 8
    css_domain_price = 7


    @staticmethod
    def get_element(id:int)->SelecElement:
        return {CommonCheckElement.id_domains_input_field: SelecElement("domain-name-input"),
                CommonCheckElement.id_domains_input_again_field: SelecElement("domain_search_input"),
                CommonCheckElement.css_search_button: SelecElement("button.btn.btn-primary", NavEleType.IsCssSelector),
                CommonCheckElement.css_not_available_target: SelecElement("p.unavailableCopy", NavEleType.IsCssSelector),
                CommonCheckElement.css_available_target: SelecElement("h3.walsheim-Black", NavEleType.IsCssSelector),
                CommonCheckElement.id_search_again_btn: SelecElement("search_form_btn"),
                CommonCheckElement.css_product_list: SelecElement("div.result.available", NavEleType.IsCssSelector), # if the domain is available, get [0]
                CommonCheckElement.class_product_name: SelecElement("domainName", NavEleType.IsClass),# select the first one
                CommonCheckElement.css_domain_price: SelecElement("span.price", NavEleType.IsCssSelector) # iterate to find the lowest
                }.get(id)