/** @odoo-module **/
import { useState} from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { SearchBarMenu } from "@web/search/search_bar_menu/search_bar_menu";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { Field } from "@web/views/fields/field";
import { Record } from "@web/model/relational_model/record";
import { RelationalModel } from "@web/model/relational_model/relational_model";
import { useModel } from "@web/model/model";
import { onWillStart, onMounted } from "@odoo/owl";
import {
    serializeDateTime,
    serializeDate,
    deserializeDateTime,
    deserializeDate,
    formatDate,
    formatDateTime
} from "@web/core/l10n/dates";

import { FormArchParser } from "@web/views/form/form_arch_parser";
import { createElement, parseXML } from "@web/core/utils/xml";

function deserializeDomain(domain, type) {
    const count = domain.length;
    if(count === 0) {
        return [false, false]
    }

    let start_dt = false, end_dt = false;
    if(count === 1) {
        let op = domain[0][1];
        if(op === ">=") {
            start_dt = domain[0][2];
        }else {
            end_dt = domain[0][2];
        }
    } else {
        start_dt = domain[0][2];
        end_dt = domain[1][2];
    }

    let fun = false;
    if(type === "datetime") {
        fun = deserializeDateTime;
    }else{
        fun = deserializeDate;
    }

    if(start_dt) {
        start_dt = fun(start_dt);
    }
    if(end_dt) {
        end_dt = fun(end_dt);
    }
    return [start_dt, end_dt]
}

// SearchBar
patch(SearchBar.prototype, {
    is_date_filter(field) {
        return field.fieldType === "datetime" || field.fieldType === "date";
    },
    format_search_date(field, date) {
        if(field.fieldType === 'datetime'){
            return formatDateTime(date);
        }
        return formatDate(date);
    },
    serialize_search_date(field, date) {
        if(field.fieldType === 'datetime'){
            return serializeDateTime(date);
        }
        return serializeDate(date);
    },
    computeFieldInfo() {
        if (!this.fieldInfo) {
            const xmlDoc = parseXML(this.env.searchModel.searchViewArch);
            const resModel = this.env.searchModel.resModel;
            let {fieldNodes} = new FormArchParser().parse(xmlDoc, {[resModel]: this.fields}, resModel);
            this.fieldInfo = fieldNodes
        }
        return this.fieldInfo;
    },
    // @override
    setup() {
        super.setup(...arguments);
        this.user = useService("user");

        // 当没有设置搜索条件时，按照odoo样式显示，目的是为了显示批量操作（作废，取消了批量操作和切换，所以没有搜索条件时，直接隐藏搜索栏）
        // if(this.user.settings.list_search_mode === "odoo" || !this.searchItemsFields.length){
        //     this.list_search_mode = 'odoo'
        //     return
        // }

        // 只判断用户配置
        this.list_search_mode = this.user.settings.list_search_mode === "classical" ? 'classical': "odoo";

        this.computeFieldInfo();
        let model = this.env.model;
        let record_data = {};
        if(this.env.model===undefined){
            model = useState(
                useModel(RelationalModel, {
                    config: {
                        "resModel": this.env.searchModel.resModel,
                        "resId": null,
                        "resIds": [
                        ],
                        "fields": this.fields,
                        "activeFields": {},
                        "isMonoRecord": true,
                        "context": this.env.searchModel.context,
                    }
                })
            );
        }
        this.env.searchModel.searchDate = {};
        var search_date = {};
        var search_fields = {};
        this.searchItemsFields.forEach(element => {
            if(this.is_date_filter(element)){
                element.widget = "search_date";
                search_date[element.fieldName] = [false, false];
            }else if(element.fieldType === "boolean"){
                element.fieldInfo = this.fieldInfo[`${element.fieldName}_0`];
                if (element.fieldInfo.widget === "boolean_selection"){
                    record_data[element.fieldName] = '';
                }
                
            }
            if (element.fieldType === "many2one"){
                search_fields[element.fieldName] = {fields: {display_name: {}}};
            }else {
                search_fields[element.fieldName] = {}
            }
        });

        var activeFields = {}
        for(let field in this.fields){
            activeFields[field] = {
                context: {},
                invisible: false,
                readonly: false,
                required: false,
                onChange: false,
                forceSave: false,
                isHandle: false
            };
        }
        let config = {
            activeFields: activeFields,
            context: this.env.searchModel.context,
            currentCompanyId: this.env.model?this.env.model.config.currentCompanyId : null,
            fields: this.fields,
            isMonoRecord: true,
            resId: null,
            resIds: [],
            resModel: this.env.searchModel.resModel,
        }

        this.env.searchModel.query.forEach(el => {
            const searchItem = this.env.searchModel.searchItems[el.searchItemId];
            if (!searchItem || !searchItem.fieldName) return
            
            if(searchItem.type === "field"){
                if(searchItem.fieldType === "many2one"){
                    record_data[searchItem.fieldName] = [el.autocompleteValue.value, el.autocompleteValue.display_name];
                }else{
                    record_data[searchItem.fieldName] = el.autocompleteValue.value;
                }
                
            }else if(searchItem.type === "filter"){
                this.env.searchModel.searchDate[searchItem.fieldName] = el.searchItemId;
                search_date[searchItem.fieldName] = deserializeDomain(searchItem.domain, searchItem.fieldType);
            }
        })
        
        this.record = new Record(model, config, record_data, {})
        this.record.search_date = search_date;

        // this.orm.call(this.env.searchModel.resModel, "onchange", [[], {}, [], search_fields], { context: this.env.searchModel.context }).then(res=>{
            // for(let field in res.value){
            //     if (typeof(res.value[field]) === "object"){
            //         record_data[field] = [res.value[field].id, res.value[field].display_name];
            //     }else{
            //         record_data[field] = res.value[field];
            //     }
            // }
            // console.log(record_data);
            // this.record._setData(record_data);
        //     this.onSearch()
        // });
        onMounted(async()=>{
            var res = await this.orm.call(this.env.searchModel.resModel, "onchange", [[], {}, [], search_fields], { context: this.env.searchModel.context });
            var data = {}
            for(let field in res.value){
                if(!res.value[field])continue;

                if (typeof(res.value[field]) === "object"){
                    data[field] = [res.value[field].id, res.value[field].display_name];
                }else if(field in search_date) {
                    
                }else{
                    data[field] = res.value[field];
                }
            }
            if(Object.values(data).length == 0)return;
            // this.record._setData(data);
            // this.env.searchModel.search();
            document.querySelector(".search_btn").click();
        })
    },
    // search
    onSearch() {
        var nextId = this.env.searchModel.nextId;
        this.searchItemsFields.forEach(element => {
            const searchItemId = element.id;
            let operator = "=";
            let value = this.record.data[element.fieldName];
            
            if(this.is_date_filter(element) && !value){
                var search_value = this.record.search_date[element.fieldName];
                const [start_date, end_date] = search_value?search_value:[false, false];
                
                var desc = element.description
                var domain = []
                if(start_date && end_date){
                    desc = `${desc} between ${this.format_search_date(element, start_date)} and ${this.format_search_date(element, end_date)}`;
                    domain = [[element.fieldName, '>=', this.serialize_search_date(element, start_date)], [element.fieldName, '<=', this.serialize_search_date(element, end_date)]]

                }else if(start_date){
                    desc = `${desc} >= ${this.format_search_date(element, start_date)}`;
                    domain = [[element.fieldName, '>=', this.serialize_search_date(element, start_date)]]
                }else if(end_date){
                    desc = `${desc} <= ${this.format_search_date(element, end_date)}`;
                    domain = [[element.fieldName, '<=', this.serialize_search_date(element, end_date)]]
                }
                
                var groupId = this.env.searchModel.searchDate[element.fieldName];
                var searchItem = groupId?this.env.searchModel.searchItems[groupId]:null;

                if(!searchItem){
                    if(domain.length > 0){
                        groupId = nextId;
                        nextId++;
                        // this.env.searchModel.splitAndAddDomain(domain);
                        this.env.searchModel.createNewFilters([{
                            description: desc,
                            domain: domain,
                            fieldName: element.fieldName,
                            fieldType: element.fieldType
                        }])
                        this.env.searchModel.searchDate[element.fieldName] = groupId;
                    }
                }else{
                    searchItem.description = desc;
                    searchItem.domain = domain;

                    const queryElem = this.env.searchModel.query.find(
                        (el) => el.searchItemId === groupId 
                    )
                    if(!queryElem){
                        this.env.searchModel.query.push({searchItemId: groupId});
                    }
                }
            } else {
                let boolean_flag = false;
                if(element.fieldType === "many2one" && value){
                    value = value[0]
                    operator = "="
                } else if(element.fieldType === "boolean"){
                    operator = "="
                    if(value === "0" || value === false){
                        value = false
                        boolean_flag = true
                    }else if (value === "1" || value === true){
                        value = true
                        boolean_flag = true
                    }else{
                        value = null
                    }
                } 
                var query = this.env.searchModel.query
                const can_search = value || boolean_flag ? true : false
                let autocompleteValue = {searchItemId, operator, value};

                if(element.filterDomain){
                    autocompleteValue.label = value
                }
                const queryElem = query.find(
                    (queryElem) => queryElem.searchItemId === searchItemId 
                );
                // if (!queryElem) {
                //     query.push({ searchItemId, autocompleteValue });
                // } else {
                //     queryElem.autocompleteValue.value = value;
                //     if(element.filterDomain){
                //         queryElem.autocompleteValue.label = value
                //     }
                // } 
                if (!queryElem && can_search) {
                    query.push({ searchItemId, autocompleteValue });
                } else if (queryElem && can_search){
                    queryElem.autocompleteValue.value = value;
                    if(element.filterDomain){
                        queryElem.autocompleteValue.label = value
                    }
                } else if (queryElem && !can_search){
                    query.splice(query.indexOf(queryElem), 1);
                }
            }
        })
        this.env.searchModel._notify();
    },
    // reset
    onReset(ev) {
        this.record._setData({})
        // document.querySelectorAll('.search_date')
        this.env.searchModel.query = [];

        for (let key in this.record.search_date) {
            this.record.search_date[key] = [false, false];
        }
        // this.env.searchModel._notify();
        this.env.searchModel.search();
    },
    // clear() {

    // },
    // toggle search mode
    onToggleMode(ev) {
        const new_search_mode = this.user.settings.list_search_mode == "odoo"? "classical": "odoo";
        this.orm.call(
            'res.users.settings', 
            'write', 
            [[this.user.settings.id], {list_search_mode: new_search_mode}], 
            {}
        ).then(location.reload());
    },
    // batch operations
    onBatchOperate(){
        this.env.searchModel.tools.showSelector = !this.env.searchModel.tools.showSelector;
    }
    
})
SearchBar.template = 'jhy.SearchBar'
SearchBar.components = {
    Field,
    SearchBarMenu,
    Dropdown,
    DropdownItem
}



