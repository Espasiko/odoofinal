# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ThemePelotazo(models.AbstractModel):
    _name = 'theme.pelotazo'
    _description = 'Pelotazo Theme Settings'
    _inherit = 'theme.utils'
    
    def _theme_pelotazo_post_copy(self, mod):
        # Disable default theme
        self.disable_view('website.option_ripple_effect')
        self.disable_view('website.option_header_sidebar')
        self.disable_view('website.option_header_hamburger')
        self.disable_view('website.option_header_vertical')
        
        # Enable custom Pelotazo theme options
        self.enable_view('theme_pelotazo.option_header_default')
        self.enable_view('theme_pelotazo.option_footer_default')
        
        # Update theme colors
        self.enable_asset('theme_pelotazo.assets_frontend')
