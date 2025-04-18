/** @odoo-module **/

import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { markup } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { useFileViewer } from "@web/core/file_viewer/file_viewer_hook";

export class ButtonField extends Component {
    static template = "ButtonField";
    static props = {
        ...standardFieldProps,
    };
    setup() {
        this.action = useService("action");
        this.dialogService = useService("dialog");
        this.fileViewer = useFileViewer();
    }

    onClick(ev) {
        ev.stopPropagation();
        let field = this.props.record.fields[this.props.name];
        var title = _t(field.string);
        var value = this.props.record.data[this.props.name];
        if(field.type==="many2one" && field.relation==="ir.attachment"){
            var file = {
                name: value[1],
                isViewable: true,
                isImage: true,
                displayName: value[1],
                downloadUrl: `web/image/${value[0]}?download=1`,
                defaultSource: `web/image/${value[0]}`
            }
    
            this.fileViewer.open(file, [file]);
        }else{
            this.dialogService.add(ConfirmationDialog, {
                title: title,
                body:  markup(`<div><label class="o_form_label" for="name_0">${title}</label>     <span>${value}</span></div>`)
            });
        }
        
    }
}

export const buttonField = {
    component: ButtonField,
    displayName: _t("查看"),
    supportedTypes: ["char"],
};

registry.category("fields").add("btn_field", buttonField);
