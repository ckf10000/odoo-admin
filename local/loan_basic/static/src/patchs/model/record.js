/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import {Record} from "@web/model/relational_model/record";


patch(Record.prototype, {

    // 去掉界面刷新自动保存
    async urgentSave() {
        // console.log(this)
        // if(this.dirty) return false;
        return true;
    }
})
