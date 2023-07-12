<script>
  if (typeof jxl === "undefined") {
    location.href = "/start";
  }
</script>

<link rel="stylesheet" type="text/css" href="/css/default/kids.css" />
<style type="text/css">
  .appearance-none {
    appearance: none;
    -moz-appearance: none;
    -webkit-appearance: none;
  }
  /**
    * https://caniuse.com/#feat=font-size-adjust
    * Firefox only
    */
  @supports (font-size-adjust: initial) {
    .select__option--margin {
      margin-left: -0.25rem !important;
    }
  }
  .bg-transparent {
    background-color: transparent;
  }
  .bg-gray-500 {
    background-color: #a0aec0 !important;
  }
  .border-gray-500 {
    border-color: #a0aec0;
  }
  .border-none {
    border-style: none;
  }
  .text-gray-500 {
    color: #a0aec0 !important;
  }
  tr.thead ~ tr > td {
    padding: 0;
  }
  th.name,
  td.name {
    max-width: 11.25rem;
    min-width: 11.25rem;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 40%;
  }
  th.block,
  td.block {
    width: 15%;
  }
  th.usage,
  td.usage {
    width: 15%;
  }
  th.time,
  td.time {
    width: 15%;
  }
  th.profile,
  td.profile {
    width: 15%;
  }
  td select {
    font-size: inherit;
    width: 100%;
  }
  .mainContent tr.separator td.separator__headline {
    background-color: #d7e9f7 !important;
    color: #7b90a0;
    font-size: 1rem;
    margin: 0;
    padding: 0.25rem 0.5rem;
    text-align: unset;
  }
  .mainContent tr.separator td.separator__headline p {
    background-color: transparent;
    margin: 0;
  }
  .mainContent td i.kisi_blocked::before {
    background-image: url("/css/rd/icons/ic_parental_lock.svg");
    margin: 0 0.125rem 0 1rem;
  }
  .mainContent td i.blocked-by-parental-control-abuse::before {
    background-image: url("/css/rd/icons/ic_blocked.svg");
    margin: 0 0.125rem 0 1rem;
  }
  .mainContent td i.blocked-by-parental-control-abuse-explanation::before {
    background-color: #006ec0;
    margin-left: 0.125rem;
    -webkit-mask-image: url(/css/rd/icons/ic_help_white.svg);
    mask-image: url(/css/rd/icons/ic_help_white.svg);
    -webkit-mask-position: top;
    mask-position: top;
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-size: 100%;
    mask-size: 100%;
  }
  .mainContent td i.blocked-by-parental-control-abuse-explanation:hover {
    cursor: pointer;
  }
  .Intro {
    margin-bottom: 2rem;
  }
  @media (min-width: 56.3125em) {
    .mainContent table.OnlyHead table {
      table-layout: auto;
    }
  }
  @media (max-width: 56.25em) {
    #uiList {
      display: block;
    }
    #uiList td {
      display: block;
      width: auto;
    }
    #uiDevices tr:not(.separator) td,
    #uiWinUsers tr:not(.separator) td,
    #uiGuests tr:not(.separator) td {
      text-align: right;
    }
    #uiDevices td[datalabel]::before,
    #uiWinUsers td[datalabel]::before,
    #uiGuests td[datalabel]::before {
      content: attr(datalabel);
      float: left;
    }
    #uiDevices td:not([datalabel]),
    #uiWinUsers td:not([datalabel]),
    #uiGuests td:not([datalabel]) {
      display: none;
    }
    #uiDevices tr td[datalabel]:last-child,
    #uiWinUsers tr td[datalabel]:last-child,
    #uiGuests tr td[datalabel]:last-child {
      padding-bottom: 0.125rem;
    }
    #uiList tr.thead {
      display: none;
    }
    th.name,
    td.name,
    th.usage,
    td.usage,
    th.time,
    td.time,
    th.profile,
    td.profile {
      max-width: initial;
      min-width: 0;
      width: auto;
    }
    #uiList td.bar[datalabel] span {
      width: 33%;
    }
    #uiList td[datalabel] select {
      max-width: 33%;
    }
    #uiList td.name[datalabel] {
      font-weight: bold;
      text-align: left;
    }
    #uiList td.name[datalabel] span {
      display: none;
    }
    .mainContent .formular.mobile_left {
      padding: 0;
    }
  }
</style>
<script type="text/javascript" src="/js/prefs.js"></script>
<script type="text/javascript" src="/js/prefHelper.js"></script>
<script type="text/javascript">
  ready.onReady(function () {
    /**
     * @description - execute a pre defined ajax post to set the block status of a device
     * @param {object} node - DOM node
     */
    function executeDeviceToBeBlockedAjaxPost(node) {
      ajaxPost(
        "/internet/kids_userlist.lua",
        "uid=" +
          jsl.getData(node, "uid") +
          "&sid=a2f486f7699c72bb" +
          "&toBeBlocked=" +
          (jsl.getData(node, "blocked") === "true" ? false : true),
        function () {
          jxl.submitForm();
        }
      );
    }
    jsl.find(".js-device-block").forEach(function (value, index) {
      jxl.addEventHandler(value, "click", function (event) {
        jsl.cancelEvent(event);
        var selectNode = jsl.findFirst(
          "select[name='profile:" + jsl.getData(value, "uid") + "']"
        );
        if (
          jsl.getData(value, "blocked") === "true" &&
          jsl.getData(
            selectNode,
            "is-device-blocked-and-is-blocked-by-profile"
          ) === "true"
        ) {
          dialog.msgBox(true, {
            Dom: html2.div(
              { class: "textarea" },
              html2.h3({}, "Internetnutzung weiterhin eingeschränkt"),
              html2.strong(
                {},
                "Die Internetnutzung bleibt nach dem Entsperren des Geräts weiterhin eingeschränkt"
              ),
              html2.p(
                {},
                jxl.sprintf(
                  'Dem Gerät ist das Zugangsprofil "%1%AccessProfileName%" zugeordnet. Die Einstellungen dieses Zugangsprofils schränken die Internetnutzung durch das Gerät weiterhin ein.',
                  selectNode.selectedOptions[0].text
                )
              ),
              html2.p(
                {},
                'Detaillierte Informationen finden Sie im Tab "Zugangsprofile"'
              )
            ),
            Buttons: [
              {
                txt: "OK",
                cb: function () {
                  executeDeviceToBeBlockedAjaxPost(value);
                },
                class: "qa-device-blocked-and-blocked-by-profile__cta",
              },
            ],
          });
        } else {
          executeDeviceToBeBlockedAjaxPost(value);
        }
      });
    });
    jsl
      .find(".js-blocked-by-parental-control-abuse-explanation")
      .forEach(function (value, index) {
        jxl.addEventHandler(value, "click", function () {
          dialog.msgBox(true, {
            Dom: html2.div(
              { class: "textarea" },
              html2.h3({}, "Netzwerkgerät blockiert"),
              html2.strong(
                {},
                "Das Netzwerkgerät wurde im Heimnetz blockiert und kann das Internet nicht nutzen."
              ),
              html2.p(
                {},
                "Grund: dem Gerät wurde eine IP-Adresse zugeordnet, die im Heimnetz bereits vergeben ist. Vergeben Sie in den Einstellungen des Geräts eine noch nicht verwendete IP-Adresse oder legen Sie dort fest, dass das Gerät seine IP-Adresse vom DHCP-Server der FRITZ!Box bezieht."
              )
            ),
            Buttons: [
              {
                txt: "Schließen",
                class: "qa-blocked-by-parental-control-abuse__cta",
              },
            ],
          });
        });
      });
    var selector = {
      buttonApply: jsl.findFirst(".js-button--apply"),
      buttonCancel: jsl.findFirst(".js-button--cancel"),
      buttonEditProfiles: jsl.findFirst(".js-button--edit-profiles"),
      selectProfiles: jsl.find(".js-select__profile"),
    };
    jxl.addEventHandler(selector.buttonEditProfiles, "click", function () {
      selector.selectProfiles.forEach(function (value, index) {
        if (
          !jsl.getData(value, "is-device-blocked-and-is-blocked-by-profile") ||
          !jsl.getData(value, "is-blocked-by-parental-control-abuse")
        ) {
          value.removeAttribute("disabled");
          jsl.removeClass(value, "appearance-none bg-transparent border-none");
        }
      });
      jsl.addClass(selector.buttonEditProfiles, "hidden");
      jsl.removeClass(selector.buttonApply, "hidden");
      jsl.removeClass(selector.buttonCancel, "hidden");
    });
  });
  var sort = sorter();
  function initTableSorter() {
    sort.init("uiList");
    sort.addTbl("uiDevices");
    sort.addTbl("uiWinUsers");
    sort.addTbl("uiGuests");
    prefHelper.oldTableHelper(jsl.get("uiList"), sort, "kidsUserList");
  }
  ready.onReady(initTableSorter);
  function addHiddenInput(form, name, value) {
    form = form || document.forms[0];
    var hidden = document.createElement("input");
    hidden.setAttribute("type", "hidden");
    hidden.name = name;
    hidden.value = value || "";
    form.appendChild(hidden);
  }
  function initOnEditHandler() {
    var confirmParams = {
      Text1: "Sie haben die Zuordnung der Zugangsprofile bearbeitet.",
      Text2: "\n",
      Text3: "Sollen die Änderungen gespeichert werden?",
      Buttons: [
        {
          txt: "Übernehmen",
          cb: onConfirmYes,
        },
        {
          txt: "Verwerfen",
          cb: onConfirmNo,
        },
      ],
    };
    var form = document.forms[0];
    var selects = form.getElementsByTagName("select");
    var dirty = false;
    var clicked = "";
    function onChange(evt) {
      var sel = jxl.evtTarget(evt);
      if (sel.name.indexOf("profile:") == 0) {
        dirty = true;
        var btnId = sel.name.replace(/^profile:/, "uiEdit:");
        var selValue = jxl.getValue(sel);
        jxl.setValue(btnId, selValue);
        jxl.setDisabled(btnId, selValue == "");
      }
    }
    function onConfirmYes() {
      addHiddenInput(form, "apply");
      addHiddenInput(form, "gotoedit", clicked);
      jxl.submitForm();
    }
    function onConfirmNo() {
      addHiddenInput(form, "edit", clicked);
      jxl.submitForm();
    }
    function onClick(evt) {
      var btn = jxl.evtTarget(evt, "submit");
      if (btn && btn.name == "edit" && dirty) {
        clicked = jxl.getValue(btn);
        dialog.messagebox(true, confirmParams);
        return jxl.cancelEvent(evt);
      }
    }
    var i = selects.length || 0;
    while (i--) {
      jxl.addEventHandler(selects[i], "change", onChange);
    }
    jxl.addEventHandler(form, "click", onClick);
  }
  ready.onReady(initOnEditHandler);
</script>

<form name="mainform" method="POST" action="/internet/kids_userlist.lua">
  <input
    type="submit"
    value=""
    style="position: absolute; top: -9999px; left: -9999px"
    name="apply"
  />
  <input type="hidden" name="sid" value="e1f486d7616c63bb" />
  <h4>Internetzugang sperren und entsperren</h4>

  <div>
    <p class="explanation__intro">
      Sperren oder entsperren Sie den Internetzugang für die Geräte in Ihrem
      Heimnetz ganz einfach über die untenstehende Tabelle.
    </p>
    <p class="explanation__main">
      Geräte mit aktiver Gerätesperre haben keinen Zugang zum Internet, können
      jedoch innerhalb Ihres Heimnetzes wie gewohnt weiter kommunizieren.
      Alternativ können Sie mittels der Zugangsprofile für jedes Gerät
      individuell festlegen wann, wie und wie lange die Internetnutzung erlaubt
      ist.<a href="/internet/kids_profilelist.lua?sid=e1f486d7616c63bb">
        &gt;&gt;&gt; zur Verwaltung der Zugangsprofile</a
      >
    </p>
    <p class="explanation__outro">
      Netzwerkgeräten mit eingeschränkter Internetnutzung wird beim Aufruf von
      http://fritz.box angezeigt, wie die Internetnutzung für dieses Gerät
      geregelt ist.
    </p>
    <br />
  </div>
  <table id="uiList" class="OnlyHead">
    <tr class="thead">
      <th class="sortable name">Gerät<span class="sort_no">&nbsp;</span></th>
      <th class="sortable block">
        Gerätesperre<span class="sort_no">&nbsp;</span>
      </th>
      <th class="sortable time">
        Online-Zeit heute<span class="sort_no">&nbsp;</span>
      </th>
      <th class="sortable usage">
        Internetnutzung<span class="sort_no">&nbsp;</span>
      </th>
      <th class="profile">Zugangsprofile</th>
    </tr>
    <tr>
      <td colspan="5">
        <table id="uiDevices" class="zebra_reverse noborder">
          <tr class="separator">
            <td datalabel="" colspan="5" class="separator__headline">
              <p>Heimnetz</p>
            </td>
          </tr>
          <tr>
            <td
              class="name"
              title="iPhone"
              datalabel="iPhone"
            >
              <i class=""></i><span>iPhone</span>
            </td>
            <td datalabel="Gerätesperre" class="block">
              <a
                class="js-device-block qa-device-block__cta"
                data-blocked="false"
                href="/internet/kids_userlist.lua"
                data-uid="landevice8516"
                >Sperren</a
              >
            </td>
            <td datalabel="Online-Zeit heute" class="bar time">Unlimited</td>
            <td datalabel="Internetnutzung" class="usage">
              <span>Unlimited</span>
            </td>
            <td datalabel="Zugangsprofile" class="profile">
              <select
                data-is-blocked-by-parental-control-abuse="false"
                class="js-select__profile qa-select__profile appearance-none bg-transparent border-none select__option--margin"
                disabled="disabled"
                name="profile:landevice7506"
              >
                <option value="filtprof1" selected>Standard</option>
                <option value="filtprof3">Unlimited</option>
                <option value="filtprof7902">Private</option>
                <option value="filtprof7264">Restricted</option>
                <option value="filtprof1075">Blacklist</option>
                <option value="filtprof0975">Whitelist</option>
              </select>
            </td>
          </tr>
          <tr>
            <td
              class="name"
              title="Alle anderen Geräte"
              datalabel="Alle anderen Geräte"
            >
              <i class=""></i><span>Alle anderen Geräte</span>
            </td>
            <td></td>
            <td datalabel="Online-Zeit heute" class="bar time">Unbegrenzt</td>
            <td datalabel="Internetnutzung" class="usage">Unlimited</td>
            <td datalabel="Zugangsprofile" title="Standard" class="profile">
              Standard
            </td>
          </tr>
        </table>
      </td>
    </tr>
    <tr>
      <td colspan="5">
        <table id="uiGuests" class="zebra_reverse noborder">
          <tr class="separator">
            <td datalabel="" colspan="5" class="separator__headline">
              <p>Gastnetz</p>
            </td>
          </tr>
          <tr>
            <td
              class="name"
              title="Alle Geräte im Gastnetz"
              datalabel="Alle Geräte im Gastnetz"
            >
              <i class=""></i><span>Alle Geräte im Gastnetz</span>
            </td>
            <td></td>
            <td datalabel="Online-Zeit heute" class="bar time">Unbegrenzt</td>
            <td datalabel="Internetnutzung" class="usage">Eingeschränkt</td>
            <td datalabel="Zugangsprofile" title="Gast" class="profile">
              Gast
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
  <br />
  <div class="btn_form">
    <button type="submit" name="cancel">Aktualisieren</button>
  </div>
  <div id="btn_form_foot">
    <button
      type="button"
      class="js-button--edit-profiles qa-button--edit-profiles"
      name="change-profiles"
    >
      Zugangsprofile ändern
    </button>
    <button
      type="submit"
      class="js-button--apply qa-button--apply hidden"
      name="apply"
    >
      Übernehmen
    </button>
    <button
      type="submit"
      class="js-button--cancel qa-button--cancel hidden"
      name="cancel"
    >
      Abbrechen
    </button>
  </div>
</form>
<input id="oldPageXhrSid" type="hidden" value="e1f486d7616c63bb" /><input
  id="fdhidedata"
  type="hidden"
  value='{"ssoSet":true,"provServ":true,"mobile":true,"liveTv":true}'
/><input
  id="oldpageactive"
  type="hidden"
  value="/internet/kids_userlist.lua"
/><input id="oldPageTitle" type="hidden" value="" /><input
  id="gHelpPage"
  type="hidden"
  value="hilfe_kindersicherung_uebersicht.html"
/>
<div id="domReady" style="display: none"></div>
