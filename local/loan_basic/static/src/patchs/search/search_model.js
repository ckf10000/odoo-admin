/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { SearchModel } from "@web/search/search_model";


patch(SearchModel.prototype, {
    setup() {
        super.setup(...arguments);
        this.user = useService("user");

        this.tools = useState({
            showSelector: this.user.settings.list_search_mode === "odoo"
        })
    }
})