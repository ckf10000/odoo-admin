/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

import { Component } from "@odoo/owl";

export class OssAttachmentField extends Component {
    static template = "OssAttachmentField";
}

export const ossAttachmentField = {
    component: OssAttachmentField,
    displayName: _t("Attachment"),
    supportedTypes: ["many2one"],
};

registry.category("fields").add("oss_attachment", ossAttachmentField);
