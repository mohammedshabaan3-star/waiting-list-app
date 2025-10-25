# الجزء الثالث من النسخة المحسنة - صفحات الإدارة

# ---------------------------- صفحات الإدارة ---------------------------- #
def admin_home() -> None:
    """الصفحة الرئيسية للإدارة"""
    user = st.session_state.user
    logo_path = Path("static/logo.png")
    if logo_path.exists():
        st.sidebar.image(str(logo_path), width=80)
    
    st.markdown("<div class='header'><h2>لوحة التحكم الإدارية</h2></div>", unsafe_allow_html=True)
    
    admin_menu = {
        "items": [
            "🏥 إدارة المستشفيات", "🧾 إدارة الطلبات", "📊 الإحصائيات",
            "📜 سجل النشاط", "🧩 إدارة الإعدادات", "👥 إدارة المستخدمين",
            "📥 إدارة ملفات التنزيل", "🔑 تغيير كلمة المرور"
        ],
        "icons": [
            "hospital", "card-list", "bar-chart-line", "clock-history",
            "gear", "people", "download", "key-fill"
        ],
        "functions": [
            admin_hospitals_ui, admin_requests_ui, admin_statistics_ui,
            admin_activity_log_ui, admin_lists_ui, admin_users_ui,
            admin_resources_ui, lambda: change_password_ui(user_id=user["id"], user_table="admins")
        ]
    }
    
    reviewer_menu = {
        "items": ["🧾 مراجعة الطلبات", "📊 الإحصائيات"],
        "icons": ["card-list", "bar-chart-line"],
        "functions": [admin_requests_ui, admin_statistics_ui]
    }
    
    menu = admin_menu if user["role"] == "admin" else reviewer_menu
    
    with st.sidebar:
        selection = option_menu(
            "القائمة",
            menu["items"] + ["🚪 تسجيل الخروج"],
            icons=menu["icons"] + ["box-arrow-right"],
            menu_icon="person-workspace",
            default_index=0
        )
    
    if selection == "🚪 تسجيل الخروج":
        st.session_state.pop("user", None)
        st.rerun()
    else:
        selected_index = (menu["items"] + ["🚪 تسجيل الخروج"]).index(selection)
        if selected_index < len(menu["functions"]):
            menu["functions"][selected_index]()

def admin_hospitals_ui() -> None:
    """إدارة المستشفيات"""
    st.markdown("<div class='subheader'>إدارة المستشفيات</div>", unsafe_allow_html=True)
    
    # استيراد من Excel
    st.markdown("#### 🔽 استيراد من ملف Excel")
    excel = st.file_uploader(
        "اختر ملف Excel يحتوي: اسم المستشفى، القطاع، المحافظة، الكود، النوع",
        type=["xlsx", "xls"]
    )
    
    if excel is not None:
        try:
            df = pd.read_excel(excel, sheet_name=0)
            required_cols = ["اسم المستشفى", "القطاع", "المحافظه", "كود المستشفى"]
            
            for c in required_cols:
                if c not in df.columns:
                    st.error(f"العمود المطلوب مفقود: {c}")
                    return
            
            if "نوع المستشفى" not in df.columns:
                df["نوع المستشفى"] = "خاص"
            
            df["username"] = df["اسم المستشفى"].apply(lambda name: generate_username(name) or "hospital")
            df["password"] = "1234"
            
            added, skipped = 0, 0
            with get_conn() as conn:
                cur = conn.cursor()
                for _, row in df.iterrows():
                    try:
                        username = row["username"]
                        base_username = username
                        counter = 1
                        
                        # ضمان فرادة اسم المستخدم
                        while True:
                            cur.execute("SELECT id FROM hospitals WHERE username=?", (username,))
                            if not cur.fetchone():
                                break
                            username = f"{base_username}{counter}"
                            counter += 1
                        
                        cur.execute("""
                            INSERT OR IGNORE INTO hospitals 
                            (name, sector, governorate, code, type, username, password_hash)
                            VALUES (?,?,?,?,?,?,?)
                        """, (
                            str(row["اسم المستشفى"]).strip(),
                            str(row["القطاع"]).strip(),
                            str(row["المحافظه"]).strip(),
                            str(row["كود المستشفى"]).strip(),
                            str(row["نوع المستشفى"]).strip() if row["نوع المستشفى"] in get_hospital_types() else get_hospital_types()[0],
                            username,
                            secure_hash(str(row["password"]).strip())
                        ))
                        
                        if cur.rowcount:
                            added += 1
                        else:
                            skipped += 1
                    except Exception as e:
                        st.warning(f"تخطي صف: {e}")
                
                conn.commit()
            
            st.success(f"تمت إضافة: {added} — تم التخطي (موجود): {skipped}")
            
            # تصدير ملف الاعتمادات
            out_path = EXPORTS_DIR / f"credentials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(out_path, index=False)
            
            with open(out_path, 'rb') as f:
                st.download_button(
                    "📥 تنزيل ملف الاعتمادات (username/password)",
                    data=f.read(),
                    file_name=out_path.name
                )
        except Exception as e:
            st.error(f"فشل الاستيراد: {e}")
    
    # إضافة مستشفى يدوياً
    st.markdown("#### ➕ إضافة مستشفى يدوياً")
    with st.expander("إضافة مستشفى جديد"):
        with st.form("add_hospital"):
            name = st.text_input("اسم المستشفى", max_chars=200)
            sector = st.text_input("القطاع", max_chars=100)
            gov = st.text_input("المحافظة", max_chars=50)
            code = st.text_input("كود المستشفى", max_chars=20)
            htype = st.text_input("نوع المستشفى", max_chars=20)
            username = st.text_input("اسم المستخدم (سيتم توليد تلقائيًا إن فارغ)", max_chars=50)
            password = st.text_input("كلمة المرور", type="password", value="1234", max_chars=100)
            
            if st.form_submit_button("إضافة"):
                if not all([name, sector, gov, code, password]):
                    st.error("يرجى ملء الحقول المطلوبة")
                else:
                    if not username:
                        username = generate_username(name) or "hospital"
                    
                    try:
                        with get_conn() as conn:
                            # ضمان فرادة اسم المستخدم
                            base_username = username
                            counter = 1
                            while conn.execute("SELECT id FROM hospitals WHERE username=?", (username,)).fetchone():
                                username = f"{base_username}{counter}"
                                counter += 1
                            
                            conn.execute("""
                                INSERT INTO hospitals (name, sector, governorate, code, type, username, password_hash)
                                VALUES (?,?,?,?,?,?,?)
                            """, (name, sector, gov, code, htype, username, secure_hash(password)))
                            conn.commit()
                        
                        st.success(f"تمت الإضافة. اسم المستخدم: {username}")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("كود المستشفى أو اسم المستخدم موجود مسبقًا")
                    except Exception as e:
                        st.error(f"خطأ في الإضافة: {e}")
    
    # قائمة المستشفيات
    st.markdown("#### 📋 قائمة المستشفيات")
    try:
        with get_conn() as conn:
            hospitals = conn.execute("SELECT * FROM hospitals ORDER BY name").fetchall()
    except Exception as e:
        st.error(f"خطأ في جلب المستشفيات: {e}")
        return
    
    if hospitals:
        df = pd.DataFrame([dict(h) for h in hospitals])
        st.dataframe(
            df[["id", "name", "sector", "governorate", "code", "type", "username"]],
            use_container_width=True,
            height=400
        )
        
        # حذف المستشفى
        with st.expander("🗑️ إدارة حذف المستشفى", expanded=False):
            st.warning("⚠️ تنبيه: الحذف نهائي ولا يمكن التراجع عنه")
            
            hospital_options = ["—"] + [f"{h['id']} — {h['name']} ({h['code']})" for h in hospitals]
            selected_hospital = st.selectbox("اختر مستشفى للحذف", hospital_options, key="delete_hospital_select")
            
            if selected_hospital != "—":
                hospital_id = int(selected_hospital.split(" — ")[0])
                hospital_name = selected_hospital.split(" — ")[1]
                
                try:
                    with get_conn() as conn:
                        request_count = conn.execute(
                            "SELECT COUNT(*) as request_count FROM requests WHERE hospital_id = ? AND deleted_at IS NULL",
                            (hospital_id,)
                        ).fetchone()['request_count']
                except Exception as e:
                    st.error(f"خطأ في التحقق من الطلبات: {e}")
                    return
                
                if request_count > 0:
                    st.error(f"❌ لا يمكن حذف المستشفى '{hospital_name}' لأنه لديه {request_count} طلب(طلبات) نشطة.")
                    st.info("يرجى حذف أو معالجة الطلبات المرتبطة أولاً قبل حذف المستشفى.")
                else:
                    st.info(f"المستشفى المحدد: {hospital_name}")
                    
                    if st.button("🗑️ حذف المستشفى", type="secondary", key="delete_hospital_btn"):
                        st.session_state['delete_hospital_id'] = hospital_id
                        st.session_state['delete_hospital_name'] = hospital_name
                    
                    # تأكيد الحذف
                    if 'delete_hospital_id' in st.session_state and st.session_state['delete_hospital_id'] == hospital_id:
                        st.error(f"⚠️ تأكيد الحذف النهائي للمستشفى: {st.session_state['delete_hospital_name']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ نعم، تأكيد الحذف", type="primary", key="confirm_delete"):
                                try:
                                    with get_conn() as conn:
                                        conn.execute("DELETE FROM hospitals WHERE id = ?", (st.session_state['delete_hospital_id'],))
                                        conn.commit()
                                    
                                    st.success(f"✅ تم حذف المستشفى '{st.session_state['delete_hospital_name']}' بنجاح")
                                    del st.session_state['delete_hospital_id']
                                    del st.session_state['delete_hospital_name']
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ حدث خطأ أثناء الحذف: {e}")
                        
                        with col2:
                            if st.button("❌ إلغاء الحذف", key="cancel_delete"):
                                del st.session_state['delete_hospital_id']
                                del st.session_state['delete_hospital_name']
                                st.success("تم إلغاء عملية الحذف")
                                st.rerun()
        
        # تعديل المستشفى
        hid = st.selectbox("اختر مستشفى للتعديل", ["—"] + [f"{h['id']} — {h['name']}" for h in hospitals], key="edit_hospital_select")
        if hid != "—":
            hid_int = int(hid.split(" — ")[0])
            edit_hospital_ui(hid_int)
    else:
        st.info("لا توجد مستشفيات مسجلة")

def edit_hospital_ui(hospital_id: int) -> None:
    """تعديل بيانات المستشفى"""
    try:
        with get_conn() as conn:
            h = conn.execute("SELECT * FROM hospitals WHERE id=?", (hospital_id,)).fetchone()
    except Exception as e:
        st.error(f"خطأ في جلب بيانات المستشفى: {e}")
        return
    
    if not h:
        st.error("المستشفى غير موجود.")
        return
    
    st.markdown(f"<div class='subheader'>تعديل: {h['name']}</div>", unsafe_allow_html=True)
    
    # checkbox خارج الـ form للمستشفيات الخاصة
    no_end_date = False
    if h["type"] != 'حكومي':
        current_no_end_admin = h["license_end"] == "غير محدد" or not h["license_end"]
        no_end_date = st.checkbox(
            "ترخيص دائم (بدون تاريخ انتهاء)",
            value=current_no_end_admin,
            key=f"admin_no_end_{hospital_id}"
        )
    
    with st.form("edit_h"):
        name = st.text_input("اسم المستشفى", h["name"], max_chars=200)
        sector = st.text_input("القطاع", h["sector"], max_chars=100)
        gov = st.text_input("المحافظة", h["governorate"], max_chars=50)
        code = st.text_input("كود المستشفى", h["code"], max_chars=20)
        htype = st.text_input("نوع المستشفى", h["type"], max_chars=20)
        address = st.text_area("العنوان بالكامل", h["address"] or "", max_chars=500)
        other_br = st.text_input("الفروع الأخرى", h["other_branches"] or "", max_chars=200)
        other_br_addr = st.text_area("عناوين الفروع الأخرى", h["other_branches_address"] or "", max_chars=500)
        
        # تواريخ الترخيص - للمستشفيات الخاصة فقط
        if htype != 'حكومي':
            lic_start = st.date_input(
                "بداية الترخيص",
                value=parse_date_safely(h["license_start"], default_value=date.today()),
                min_value=date(1900, 1, 1),
                max_value=date(2100, 12, 31)
            )
            
            if not no_end_date:
                lic_end = st.date_input(
                    "تاريخ انتهاء الترخيص",
                    value=parse_date_safely(h["license_end"], default_value=date.today()),
                    min_value=date(1900, 1, 1),
                    max_value=date(2100, 12, 31)
                )
            else:
                lic_end = "غير محدد"
        else:
            lic_start = None
            lic_end = None
            st.info("المستشفيات الحكومية غير مطالبة بتواريخ الترخيص")
        
        manager = st.text_input("اسم مدير المستشفى", h["manager_name"] or "", max_chars=100)
        manager_phone = st.text_input("رقم هاتف المدير", h["manager_phone"] or "", max_chars=20)
        license_no = st.text_input("رقم الترخيص", h["license_number"] or "", max_chars=50)
        username = st.text_input("اسم المستخدم", h["username"], max_chars=50)
        new_pw = st.text_input("كلمة مرور جديدة (اختياري)", type="password", max_chars=100)
        
        if st.form_submit_button("حفظ التعديل"):
            try:
                q = ("UPDATE hospitals SET name=?, sector=?, governorate=?, code=?, type=?, "
                     "address=?, other_branches=?, other_branches_address=?, license_start=?, "
                     "license_end=?, manager_name=?, manager_phone=?, license_number=?, username=?")
                
                # تحضير قيمة lic_end
                lic_end_value = None
                if htype != 'حكومي':
                    if lic_end == "غير محدد":
                        lic_end_value = "غير محدد"
                    elif lic_end:
                        lic_end_value = str(lic_end)
                
                params = [
                    name, sector, gov, code, htype, address, other_br, other_br_addr,
                    str(lic_start) if lic_start else None,
                    lic_end_value,
                    manager, manager_phone, license_no, username
                ]
                
                if new_pw:
                    q += ", password_hash=?"
                    params.append(secure_hash(new_pw))
                
                q += " WHERE id=?"
                params.append(hospital_id)
                
                with get_conn() as conn:
                    conn.execute(q, tuple(params))
                    conn.commit()
                
                st.success("تم التعديل بنجاح")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("كود المستشفى أو اسم المستخدم مستخدم مسبقًا")
            except Exception as e:
                st.error(f"خطأ في التعديل: {e}")

def admin_requests_ui() -> None:
    """إدارة الطلبات"""
    st.markdown("<div class='subheader'>إدارة الطلبات</div>", unsafe_allow_html=True)
    st.markdown("#### تصفية الطلبات")
    
    try:
        with get_conn() as conn:
            services = conn.execute("SELECT id, name FROM services ORDER BY name").fetchall()
            hospitals = conn.execute("SELECT id, name FROM hospitals ORDER BY name").fetchall()
            sectors = conn.execute("SELECT DISTINCT sector FROM hospitals ORDER BY sector").fetchall()
    except Exception as e:
        st.error(f"خطأ في جلب بيانات التصفية: {e}")
        return
    
    service_options = ["الكل"] + [s["name"] for s in services]
    hospital_options = ["الكل"] + [h["name"] for h in hospitals]
    sector_filter_options = ["الكل"] + [s["sector"] for s in sectors]
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        selected_service = st.selectbox("الخدمة", service_options)
    with col2:
        selected_hospital = st.selectbox("المستشفى", hospital_options)
    with col3:
        request_id_input = st.text_input("ID الطلب (رقم)")
    with col4:
        selected_hospital_sector = st.selectbox("القطاع", sector_filter_options)
    with col5:
        start_date = st.date_input("تاريخ البدء", value=None, format="YYYY/MM/DD")
    with col6:
        end_date = st.date_input("تاريخ الانتهاء", value=None, format="YYYY/MM/DD")
    
    status_col, deleted_col = st.columns(2)
    with status_col:
        status_options = ["الكل"] + [s for s in get_request_statuses() if s != "طلب غير مكتمل"] + ["طلب غير مكتمل"]
        status = st.selectbox("الحالة", status_options)
    with deleted_col:
        show_deleted = st.checkbox("عرض المحذوفات؟")
    
    # بناء الاستعلام
    q = """SELECT r.id, h.name AS hospital, h.code AS code, h.type AS hospital_type,
                  s.name AS service, r.age_category, r.status, r.created_at, r.deleted_at
           FROM requests r
           JOIN hospitals h ON h.id=r.hospital_id
           JOIN services s ON s.id=r.service_id
           WHERE 1=1"""
    params = []
    
    if not show_deleted:
        q += " AND r.deleted_at IS NULL"
    if status != "الكل":
        q += " AND r.status=?"
        params.append(status)
    if selected_service != "الكل":
        q += " AND s.name=?"
        params.append(selected_service)
    if selected_hospital != "الكل":
        q += " AND h.name=?"
        params.append(selected_hospital)
    if request_id_input and request_id_input.isdigit():
        q += " AND r.id=?"
        params.append(int(request_id_input))
    if selected_hospital_sector != "الكل":
        q += " AND h.sector=?"
        params.append(selected_hospital_sector)
    if start_date:
        q += " AND DATE(r.created_at) >= ?"
        params.append(start_date.isoformat())
    if end_date:
        q += " AND DATE(r.created_at) <= ?"
        params.append(end_date.isoformat())
    
    q += " ORDER BY r.created_at DESC"
    
    try:
        with get_conn() as conn:
            rows = conn.execute(q, tuple(params)).fetchall()
    except Exception as e:
        st.error(f"خطأ في جلب الطلبات: {e}")
        return
    
    df = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()
    st.dataframe(df, use_container_width=True)
    
    if rows:
        pick = st.selectbox("اختر طلبًا لإدارته", ["—"] + [str(r["id"]) for r in rows])
        if pick != "—":
            admin_request_detail_ui(int(pick))

def admin_request_detail_ui(request_id: int) -> None:
    """تفاصيل الطلب للإدارة"""
    try:
        with get_conn() as conn:
            r = conn.execute("""
                SELECT r.*, h.name AS hospital_name, h.code AS hospital_code,
                       h.type AS hospital_type, s.name AS service_name,
                       h.manager_name, h.manager_phone, h.license_start, h.license_end
                FROM requests r
                JOIN hospitals h ON h.id=r.hospital_id
                JOIN services s ON s.id=r.service_id
                WHERE r.id=?
            """, (request_id,)).fetchone()
            
            docs = conn.execute(
                "SELECT * FROM documents WHERE request_id=? ORDER BY id",
                (request_id,)
            ).fetchall()
    except Exception as e:
        st.error(f"خطأ في جلب تفاصيل الطلب: {e}")
        return
    
    if not r:
        st.error("الطلب غير موجود.")
        return
    
    st.markdown(f"<div class='subheader'>إدارة الطلب #{request_id}</div>", unsafe_allow_html=True)
    
    # عرض بيانات المستشفى
    st.markdown("#### بيانات المستشفى")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**اسم المستشفى:** {r['hospital_name']}")
        st.write(f"**كود المستشفى:** {r['hospital_code']}")
        st.write(f"**نوع المستشفى:** {r['hospital_type']}")
    with col2:
        st.write(f"**مدير المستشفى:** {r['manager_name'] or 'غير محدد'}")
        st.write(f"**هاتف المدير:** {r['manager_phone'] or 'غير محدد'}")
        if r['hospital_type'] != 'حكومي' and r['license_start']:
            st.write(f"**بداية الترخيص:** {r['license_start']}")
    
    st.markdown("---")
    st.write(f"**الخدمة:** {r['service_name']} — **الفئة:** {r['age_category']} — **الحالة الحالية:** {r['status']}")
    
    colA, colB = st.columns([2, 3])
    with colA:
        current_statuses = get_request_statuses()
        new_status = st.selectbox(
            "الحالة",
            current_statuses,
            index=current_statuses.index(r['status']) if r['status'] in current_statuses else 0
        )
        note = st.text_area("ملاحظة إدارية", r['admin_note'] or "", max_chars=1000)
        
        if st.button("حفظ الحالة"):
            try:
                with get_conn() as conn:
                    closed_at = None
                    updated_at = datetime.now().isoformat()
                    
                    if is_final_status(new_status):
                        closed_at = datetime.now().isoformat()
                        conn.execute(
                            "UPDATE requests SET status=?, admin_note=?, closed_at=?, updated_at=? WHERE id=?",
                            (new_status, note, closed_at, updated_at, request_id)
                        )
                    else:
                        if r['closed_at'] and not is_final_status(new_status):
                            conn.execute(
                                "UPDATE requests SET status=?, admin_note=?, closed_at=NULL, updated_at=? WHERE id=?",
                                (new_status, note, updated_at, request_id)
                            )
                        else:
                            conn.execute(
                                "UPDATE requests SET status=?, admin_note=?, updated_at=? WHERE id=?",
                                (new_status, note, updated_at, request_id)
                            )
                    conn.commit()
                
                log_activity("تحديث حالة طلب", f"طلب رقم: {request_id}، الحالة الجديدة: {new_status}")
                st.success("تم الحفظ")
                st.cache_data.clear()
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error(f"خطأ في حفظ الحالة: {e}")
    
    with colB:
        if st.button("تنزيل كل الملفات (ZIP)"):
            try:
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for d in docs:
                        if d['file_path'] and validate_file_path(d['file_path']) and os.path.exists(d['file_path']):
                            try:
                                zf.write(
                                    d['file_path'],
                                    arcname=f"{safe_filename(d['doc_type'])}{Path(d['file_path']).suffix}"
                                )
                            except Exception:
                                pass
                buf.seek(0)
                st.download_button(
                    "📥 تحميل الملفات",
                    data=buf,
                    file_name=f"request_{request_id}_files.zip"
                )
            except Exception as e:
                st.error(f"خطأ في إنشاء ملف ZIP: {e}")
    
    # إدارة المستندات
    st.markdown("##### المستندات")
    for d in docs:
        c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 2, 2, 3, 3])
        with c1:
            display_name = d['display_name'] or d['doc_type']
            st.write(display_name)
            st.caption("مطلوب" if d['required'] else "اختياري")
            req_toggle_admin = st.checkbox(
                "مطلوب؟",
                value=bool(d['required']),
                key=f"req_admin_{d['id']}"
            )
        
        with c2:
            sat_toggle = st.checkbox(
                "مستوفى؟",
                value=bool(d['satisfied']),
                key=f"sat_{d['id']}"
            )
        
        with c3:
            render_file_downloader(d, key_prefix=f"dl_admin_{d['id']}")
        
        with c4:
            if d["file_path"]:
                if st.button("حذف", key=f"del_{d['id']}"):
                    delete_document_file(d)
                    st.rerun()
        
        with c5:
            comment = st.text_input(
                "تعليق",
                value=d['admin_comment'] or "",
                key=f"cm_{d['id']}",
                max_chars=500
            )
        
        with c6:
            if st.button("حفظ", key=f"save_{d['id']}"):
                try:
                    with get_conn() as conn:
                        new_required_value = 1 if req_toggle_admin else 0
                        conn.execute(
                            "UPDATE documents SET required=?, satisfied=?, admin_comment=? WHERE id=?",
                            (new_required_value, 1 if sat_toggle else 0, comment, d['id'])
                        )
                        conn.commit()
                    st.success("تم التحديث")
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ في التحديث: {e}")
    
    # الإجراءات
    st.markdown("##### الإجراءات")
    cols = st.columns(3)
    with cols[0]:
        if st.button("❌ حذف الطلب نهائيًا"):
            try:
                delete_request(request_id, docs)
                log_activity("حذف طلب نهائي", f"طلب رقم: {request_id}")
                st.success("تم الحذف النهائي. يمكن للمستشفى تقديم طلب جديد لنفس الخدمة الآن.")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"خطأ في الحذف: {e}")
    
    with cols[1]:
        if st.button("🔄 استرجاع كـ 'إعادة تقديم'"):
            try:
                with get_conn() as conn:
                    conn.execute(
                        "UPDATE requests SET status='إعادة تقديم', deleted_at=NULL, updated_at=? WHERE id=?",
                        (datetime.now().isoformat(), request_id)
                    )
                    conn.commit()
                log_activity("استرجاع طلب", f"طلب رقم: {request_id}")
                st.success("تم الاسترجاع")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"خطأ في الاسترجاع: {e}")
    
    with cols[2]:
        if st.button("🔒 إغلاق الطلب"):
            try:
                with get_conn() as conn:
                    final_status = "مغلق"
                    conn.execute(
                        "UPDATE requests SET status=?, closed_at=?, updated_at=? WHERE id=?",
                        (final_status, datetime.now().isoformat(), datetime.now().isoformat(), request_id)
                    )
                    conn.commit()
                log_activity("إغلاق طلب", f"طلب رقم: {request_id}")
                st.success("تم الإغلاق — يمكن تقديم طلب جديد")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"خطأ في الإغلاق: {e}")

def admin_activity_log_ui() -> None:
    """واجهة عرض سجل نشاط المستخدمين"""
    st.markdown("<div class='subheader'>📜 سجل نشاط المستخدمين</div>", unsafe_allow_html=True)
    
    # فلاتر البحث
    st.markdown("#### تصفية السجلات")
    col1, col2, col3 = st.columns(3)
    with col1:
        search_user = st.text_input("اسم المستخدم", max_chars=50)
    with col2:
        try:
            with get_conn() as conn:
                actions = [r['action'] for r in conn.execute("SELECT DISTINCT action FROM activity_log ORDER BY action").fetchall()]
        except Exception as e:
            st.error(f"خطأ في جلب الإجراءات: {e}")
            actions = []
        selected_action = st.selectbox("نوع الإجراء", ["الكل"] + actions)
    with col3:
        date_filter = st.date_input("تاريخ محدد", value=None)
    
    # بناء الاستعلام
    query = "SELECT timestamp, username, user_role, action, details FROM activity_log WHERE 1=1"
    params = []
    
    if search_user:
        query += " AND username LIKE ?"
        params.append(f"%{search_user}%")
    if selected_action != "الكل":
        query += " AND action = ?"
        params.append(selected_action)
    if date_filter:
        query += " AND DATE(timestamp) = ?"
        params.append(date_filter.isoformat())
    
    query += " ORDER BY timestamp DESC LIMIT 500"
    
    # عرض النتائج
    try:
        with get_conn() as conn:
            logs = conn.execute(query, params).fetchall()
    except Exception as e:
        st.error(f"خطأ في جلب السجلات: {e}")
        return
    
    if logs:
        df = pd.DataFrame([dict(log) for log in logs])
        st.dataframe(df, use_container_width=True, height=600)
    else:
        st.info("لا توجد سجلات تطابق معايير البحث.")

def admin_statistics_ui() -> None:
    """واجهة الإحصائيات"""
    st.markdown("<div class='subheader'>الإحصائيات</div>", unsafe_allow_html=True)
    
    # تصفية الإحصائيات
    st.markdown("#### تصفية الإحصائيات")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sectors = get_sectors()
        selected_sector = st.selectbox("القطاع", ["الكل"] + sectors)
    
    with col2:
        try:
            with get_conn() as conn:
                services = [s['name'] for s in conn.execute("SELECT name FROM services WHERE active=1").fetchall()]
        except Exception as e:
            st.error(f"خطأ في جلب الخدمات: {e}")
            services = []
        selected_service = st.selectbox("الخدمة", ["الكل"] + services)
    
    with col3:
        hospital_types = get_hospital_types()
        selected_type = st.selectbox("نوع المستشفى", ["الكل"] + hospital_types)
    
    with col4:
        statuses = get_request_statuses()
        selected_status = st.selectbox("حالة الطلب", ["الكل"] + statuses)
    
    col5, col6 = st.columns(2)
    with col5:
        start_date = st.date_input("من تاريخ", value=None)
    with col6:
        end_date = st.date_input("إلى تاريخ", value=None)
    
    # بناء شروط الاستعلام
    where_conditions = ["r.deleted_at IS NULL"]
    params = []
    
    if selected_sector != "الكل":
        where_conditions.append("h.sector = ?")
        params.append(selected_sector)
    if selected_service != "الكل":
        where_conditions.append("s.name = ?")
        params.append(selected_service)
    if selected_type != "الكل":
        where_conditions.append("h.type = ?")
        params.append(selected_type)
    if selected_status != "الكل":
        where_conditions.append("r.status = ?")
        params.append(selected_status)
    if start_date:
        where_conditions.append("DATE(r.created_at) >= ?")
        params.append(start_date.isoformat())
    if end_date:
        where_conditions.append("DATE(r.created_at) <= ?")
        params.append(end_date.isoformat())
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    
    try:
        with get_conn() as conn:
            # إحصائيات حسب الحالة
            query_status = f"""
                SELECT r.status, COUNT(*) as count
                FROM requests r
                JOIN hospitals h ON r.hospital_id = h.id
                JOIN services s ON r.service_id = s.id
                WHERE {where_clause}
                GROUP BY r.status
                ORDER BY count DESC
            """
            status_stats = conn.execute(query_status, params).fetchall()
            
            # إحصائيات حسب الخدمة
            query_service = f"""
                SELECT s.name, COUNT(*) as count
                FROM requests r
                JOIN hospitals h ON r.hospital_id = h.id
                JOIN services s ON r.service_id = s.id
                WHERE {where_clause}
                GROUP BY s.name
                ORDER BY count DESC
            """
            service_stats = conn.execute(query_service, params).fetchall()
            
            # إحصائيات حسب نوع المستشفى
            query_type = f"""
                SELECT h.type, COUNT(*) as count
                FROM requests r
                JOIN hospitals h ON r.hospital_id = h.id
                JOIN services s ON r.service_id = s.id
                WHERE {where_clause}
                GROUP BY h.type
                ORDER BY count DESC
            """
            type_stats = conn.execute(query_type, params).fetchall()
            
            # إحصائيات حسب القطاع
            query_sector = f"""
                SELECT h.sector, COUNT(*) as count
                FROM requests r
                JOIN hospitals h ON r.hospital_id = h.id
                JOIN services s ON r.service_id = s.id
                WHERE {where_clause}
                GROUP BY h.sector
                ORDER BY count DESC
            """
            sector_stats = conn.execute(query_sector, params).fetchall()
    except Exception as e:
        st.error(f"خطأ في جلب الإحصائيات: {e}")
        return
    
    # عرض الإحصائيات
    st.markdown("#### إحصائيات مفصلة")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='stats-card'>", unsafe_allow_html=True)
        st.markdown("<div class='stats-header'>حسب الحالة</div>", unsafe_allow_html=True)
        for stat in status_stats:
            st.markdown(
                f"<div class='stats-item'><span class='stats-label'>{stat['status']}</span><span class='stats-value'>{stat['count']}</span></div>",
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='stats-card'>", unsafe_allow_html=True)
        st.markdown("<div class='stats-header'>حسب نوع المستشفى</div>", unsafe_allow_html=True)
        for stat in type_stats:
            st.markdown(
                f"<div class='stats-item'><span class='stats-label'>{stat['type']}</span><span class='stats-value'>{stat['count']}</span></div>",
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='stats-card'>", unsafe_allow_html=True)
        st.markdown("<div class='stats-header'>حسب الخدمة</div>", unsafe_allow_html=True)
        for stat in service_stats:
            st.markdown(
                f"<div class='stats-item'><span class='stats-label'>{stat['name']}</span><span class='stats-value'>{stat['count']}</span></div>",
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='stats-card'>", unsafe_allow_html=True)
        st.markdown("<div class='stats-header'>حسب القطاع</div>", unsafe_allow_html=True)
        for stat in sector_stats:
            st.markdown(
                f"<div class='stats-item'><span class='stats-label'>{stat['sector']}</span><span class='stats-value'>{stat['count']}</span></div>",
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)
    
    # الرسوم البيانية
    try:
        st.markdown("---")
        st.markdown("#### 📊 الإحصائيات البيانية")
        
        status_data = [dict(row) for row in status_stats]
        type_data = [dict(row) for row in type_stats]
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            if len(status_data) > 0:
                try:
                    status_df = pd.DataFrame(status_data)
                    fig_status = px.pie(
                        status_df,
                        values='count',
                        names='status',
                        title='توزيع الطلبات حسب الحالة',
                        color_discrete_sequence=px.colors.sequential.Blues_r
                    )
                    fig_status.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_status, use_container_width=True)
                except Exception as e:
                    st.warning(f"خطأ في إنشاء الرسم البياني: {e}")
            else:
                st.info("لا توجد بيانات للحالات")
        
        with chart_col2:
            if len(type_data) > 0:
                try:
                    type_df = pd.DataFrame(type_data)
                    fig_type = px.bar(
                        type_df,
                        x='type',
                        y='count',
                        title='عدد الطلبات حسب نوع المستشفى',
                        color='type',
                        color_discrete_sequence=['#1f77b4', '#ff7f0e']
                    )
                    fig_type.update_layout(xaxis_title="نوع المستشفى", yaxis_title="العدد")
                    st.plotly_chart(fig_type, use_container_width=True)
                except Exception as e:
                    st.warning(f"خطأ في إنشاء الرسم البياني: {e}")
            else:
                st.info("لا توجد بيانات لأنواع المستشفيات")
    except Exception as e:
        st.warning(f"حدث خطأ أثناء إنشاء الرسوم البيانية: {e}")