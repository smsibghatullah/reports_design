from odoo import models, fields, api
from datetime import timedelta
from googletrans import Translator


from collections import defaultdict

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_date_formatted = fields.Char(
        compute='_compute_formatted_dates', string='Formatted Order Date', store=False
    )
    validity_date_formatted = fields.Char(
        compute='_compute_formatted_dates', string='Formatted Expiration Date', store=False
    )

    def _compute_formatted_dates(self):
        for record in self:
            record.order_date_formatted = record.date_order.strftime('%d.%m.%Y') if record.date_order else ''
            record.validity_date_formatted = record.validity_date.strftime('%d.%m.%Y') if record.validity_date else ''


    def subtract_discount_from_tax(self):
        if self.env.context.get('skip_subtract_discount_from_tax'):
            return

        for order in self:
            total_tax = 0
            discount_amt = 0
            order_untaxed_after_discount = order.amount_untaxed  # Initialize with untaxed amount

            for line in order.order_line:
                # Calculate price after line discount
                if line.discount_method == 'fix':
                    price_after_discount = (line.price_unit * line.product_uom_qty) - line.discount_amount
                elif line.discount_method == 'per':
                    price_after_discount = (line.price_unit * line.product_uom_qty) * (1 - (line.discount_amount or 0.0) / 100.0)
                else:
                    price_after_discount = line.price_unit * line.product_uom_qty

                taxes = line.tax_id.compute_all(price_after_discount, line.order_id.currency_id, 1, product=line.product_id, partner=line.order_id.partner_shipping_id)

                line.update({
                    # 'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })

                total_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))

            if order.discount_type != 'line':
                if order.discount_method == 'per':
                    order_untaxed_after_discount -= order.amount_untaxed * (order.discount_amount or 0.0) / 100.0
                elif order.discount_method == 'fix':
                    order_untaxed_after_discount -= order.discount_amount

            order.with_context(skip_subtract_discount_from_tax=True).update({
                'amount_total': order_untaxed_after_discount + total_tax
            })






    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        order.subtract_discount_from_tax()

        return order

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        self.subtract_discount_from_tax()
        
        return res


    def get_aggregated_taxes(self):
        aggregated_taxes = defaultdict(lambda: {'amount': 0.0, 'base': 0.0})

        for order in self:
            total_order_amount = sum(line.price_unit * line.product_uom_qty for line in order.order_line)

            for line in order.order_line:
                # Calculate price after line discount if discount type is 'line'
                if order.discount_type == 'line':
                    if line.discount_method == 'fix':
                        line_discount_amount = line.discount_amount
                    elif line.discount_method == 'per':
                        line_discount_amount = (line.discount_amount / 100.0) * (line.price_unit * line.product_uom_qty)
                    else:
                        line_discount_amount = 0.0

                    price_after_discount = (line.price_unit * line.product_uom_qty) - line_discount_amount
                    print(price_after_discount,"llllllllllllllllllllllllllllllllllllll")

                # Calculate price after global discount if discount type is 'global'
                elif order.discount_type == 'global':
                    price_after_line_discount = line.price_unit * line.product_uom_qty
                    if total_order_amount == 0:
                        proportionate_global_discount = 0  # or handle accordingly, e.g., log a warning
                    else:
                        proportionate_global_discount = (price_after_line_discount / total_order_amount) * order.discount_amt
                    price_after_discount = price_after_line_discount - proportionate_global_discount
                    print(price_after_discount,"gggggggggggggggggggggggggggggggggggggggggggg")

                else:
                    price_after_discount = line.price_unit * line.product_uom_qty

                taxes = line.tax_id.compute_all(price_after_discount, line.order_id.currency_id, 1, product=line.product_id, partner=line.order_id.partner_shipping_id)

                for tax in line.tax_id:
                    user_language = order.partner_id.lang  
                    if user_language == 'lv_LV':  
                        key = tax.name
                    elif user_language == 'en_US':
                        key = tax.tax_name_in_english
                    tax_amount = (tax.amount / 100.0) * price_after_discount
                    aggregated_taxes[key]['amount'] += tax_amount
                    aggregated_taxes[key]['base'] += price_after_discount

        return aggregated_taxes
    
   

class AccountTax(models.Model):
    _inherit = 'account.tax'

    tax_name_in_english = fields.Char(string="Tax in Latvian", compute='_compute_tax_name_in_english', store=True)

    @api.depends('name')
    def _compute_tax_name_in_english(self):
        translator = Translator()
        for tax in self:
            if tax.name:
                translation = translator.translate(tax.name, src='lv', dest='en')
                print(translation.text,"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
                tax.tax_name_in_english = translation.text
            else:
                tax.tax_name_in_english = ''

    @api.model
    def create(self, vals):
        record = super(AccountTax, self).create(vals)
        if 'name' in vals:
            record._compute_tax_name_in_english()
        return record

    def write(self, vals):
        result = super(AccountTax, self).write(vals)
        if 'name' in vals:
            self._compute_tax_name_in_english()
        return result