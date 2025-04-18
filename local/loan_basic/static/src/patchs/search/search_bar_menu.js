/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { SearchBarMenu } from "@web/search/search_bar_menu/search_bar_menu";


patch(SearchBarMenu.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.user = useService("user");
        let search_fields = Object.values(this.env.searchModel.searchItems).find((f) => f.type === "field");
        this.canToggleMode = search_fields && Object.keys(search_fields).length > 0;
    },
    async onToggleMode(ev) {
        const new_search_mode = this.user.settings.list_search_mode == "odoo"? "classical": "odoo";
        await this.orm.call(
            'res.users.settings', 
            'write', 
            [[this.user.settings.id], {list_search_mode: new_search_mode}], 
            {}
        ).then(location.reload());
    }
})

SearchBarMenu.template="jhy.SearchBarMenu"