The error "Odoo 18 custom field x_notas_inventario does not exist in product.product model" indicates that Odoo cannot find the specified field `x_notas_inventario` within the `product.product` model, particularly in Odoo version 18. This can occur despite the field seemingly being defined in your custom module. Several factors can cause this, and the solution depends on the specific root cause.

**Troubleshooting Steps and Solutions:**

1.  **View Definition Errors:** The most common cause is that the field is referenced in a view (form, tree, etc.) but is either not correctly defined in the model or the view is not properly updated [^4], [^6].

    *   **Solution:** Identify the view(s) where `x_notas_inventario` is used. Navigate to *Settings -> Technical -> User Interface -> Views*. Search for views related to `product.product` or containing `x_notas_inventario` in their architecture [^6].  Once found, carefully examine the XML code of the view. Ensure that the field name is spelled correctly and that the view is correctly inheriting from the base `product.product` view if it's an inherited view. If the field was recently deleted, remove the reference to it from the view [^6].
    *   **Example:** If you have a form view for `product.product` and it contains `<field name="x_notas_inventario"/>`, verify that the field is correctly defined in your `product.product` model.
    *   **Odoo 18 Specific:** In Odoo 18, pay close attention to nested classes and views. If `x_notas_inventario` is part of a nested class, ensure the view correctly references it through the appropriate relational field.  For example, if you're using a One2many field, the `<tree>` tag might need to be replaced with `<list>` in the XML view [^2].

2.  **Module Upgrade Issues:** Odoo sometimes fails to properly update modules, especially after adding or modifying fields [^3], [^5].

    *   **Solution:** Upgrade the module containing the `product.product` model and the `x_notas_inventario` field.  Do this from the command line using `odoo-bin -u <module_name>` or `odoo-bin -u all` to update all modules [^4].  Restart the Odoo service after upgrading.  Sometimes, a simple restart through the UI isn't sufficient [^3].
    *   **Explanation:** Upgrading from the command line forces Odoo to re-evaluate the module's structure and update the database schema accordingly.
    *   **Data Loss Risk:** Uninstalling and reinstalling the module *can* resolve the issue, but it may lead to data loss, so it should be a last resort [^3], [^5].

3.  **Model Definition Problems:** The field might not be correctly defined in the `product.product` model [^1].

    *   **Solution:** Check your `models.py` file where you're inheriting from `product.product`. Ensure the field `x_notas_inventario` is defined with the correct data type (e.g., `fields.Text()`, `fields.Char()`, `fields.Integer()`).
    *   **Example:**

    ```python
    from odoo import models, fields

    class ProductProduct(models.Model):
        _inherit = 'product.product'

        x_notas_inventario = fields.Text(string="Inventory Notes")
    ```

    *   **Inheritance Issues:** If you're using `_name` instead of `_inherit`, it can cause problems.  Use `_inherit = 'product.product'` to extend the existing model [^1].

4.  **Database Inconsistencies:** In rare cases, the Odoo database might not reflect the changes made in your code [^4].

    *   **Solution:** Connect to the PostgreSQL database using `psql` and manually check if the column `x_notas_inventario` exists in the `product_product` table.  If it doesn't, it indicates a problem with the module upgrade process. You can try manually adding the column using `ALTER TABLE product_product ADD COLUMN x_notas_inventario TEXT;` (adjust the data type as needed). **Warning:** This should be done with caution and only if you understand the database schema.  Back up your database before making manual changes [^4].

5.  **Caching Issues:** Odoo's caching mechanism can sometimes cause outdated information to be used [^3].

    *   **Solution:** Clear Odoo's cache. Restarting the Odoo service usually clears the cache. You can also try refreshing your browser's cache.

6.  **Incorrect XPath in Inherited Views:** If you are inheriting a view and using XPath to add the field, the XPath might be incorrect, causing the field not to be found during view rendering [^7].

    *   **Solution:** Carefully review your XPath expressions in the view definition. Use a precise and unambiguous XPath to locate the correct position for inserting the field.  Sometimes, seemingly correct XPaths fail, and you might need to use alternative, more specific XPaths [^7].

7.  **Typos and Case Sensitivity:** Double-check for typos in the field name (`x_notas_inventario`) in both the model definition and the view definitions. Odoo is case-sensitive [^4].

**Conflicting Information and Discrepancies:**

The sources don't present significant conflicting information, but they emphasize different aspects of the problem. Some sources [^1], [^3], [^5] highlight module upgrade issues, while others [^4], [^6] focus on view definition errors. The best approach is to systematically check all potential causes.

**Unclear Aspects and Further Research:**

Without access to your specific code (models.py and views.xml), it's impossible to pinpoint the exact cause. Providing code snippets would allow for a more precise diagnosis. It would also be helpful to know the exact steps you took when creating and installing the custom module.

**Summary:**

The "Field 'x_notas_inventario' does not exist in model 'product.product'" error in Odoo 18 can be resolved by systematically checking the model definition, view definitions, module upgrade process, database consistency, and potential caching issues. Start by examining the view definitions and ensuring the field is correctly referenced. Then, upgrade the module from the command line. If the problem persists, investigate the model definition and database.

**Sources:**

[^1]: [https://www.odoo.com/forum/help-1/custom-field-error-field-does-not-exist-171666](https://www.odoo.com/forum/help-1/custom-field-error-field-does-not-exist-171666)
[^2]: [https://www.odoo.com/forum/help-1/odoo-18-custom-module-error-on-nested-class-view-275449](https://www.odoo.com/forum/help-1/odoo-18-custom-module-error-on-nested-class-view-275449)
[^3]: [https://www.odoo.com/forum/help-1/field-does-not-exists-on-model-error-when-upgrading-custom-modules-in-odoo-16-218714](https://www.odoo.com/forum/help-1/field-does-not-exists-on-model-error-when-upgrading-custom-modules-in-odoo-16-218714)
[^4]: [https://www.odoo.com/forum/help-1/how-to-avoid-field-does-not-exist-in-model-error-when-deleting-a-field-264065](https://www.odoo.com/forum/help-1/how-to-avoid-field-does-not-exist-in-model-error-when-deleting-a-field-264065)
[^5]: [https://www.reddit.com/r/Odoo/comments/1b3yq1f/field_doesnt_exist_in_model/](https://www.reddit.com/r/Odoo/comments/1b3yq1f/field_doesnt_exist_in_model/)
[^6]: [https://www.odoo.com/forum/help-1/error-field-does-not-exist-164564](https://www.odoo.com/forum/help-1/error-field-does-not-exist-164564)
[^7]: [https://www.odoo.com/forum/help-1/field-does-not-exist-error-on-inherited-view-125604](https://www.odoo.com/forum/help-1/field-does-not-exist-error-on-inherited-view-125604)