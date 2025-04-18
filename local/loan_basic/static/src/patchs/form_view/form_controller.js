/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import {FormController} from "@web/views/form/form_controller";


patch(FormController.prototype, {

    // 去掉离开界面自动保存
    async beforeLeave() {
        // if (this.model.root.dirty) {
        //     return this.model.root.save({
        //         reload: false,
        //         onError: this.onSaveError.bind(this),
        //     });
        // }
    }
})
