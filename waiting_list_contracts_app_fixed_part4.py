# الجزء الرابع والأخير من النسخة المحسنة - باقي وظائف الإدارة والدالة الرئيسية

def admin_lists_ui() -> None:
    """إدارة الخدمات وأنواع المستشفيات"""
    st.markdown("<div class='subheader'>إدارة الخدمات وأنواع المستشفيات</div>", unsafe_allow_html=True)
    
    # إدارة الخدمات
    st.markdown("#### 🧩 الخدمات")
    try:
        with get_conn() as conn:
            services = conn.execute("SELECT * FROM services ORDER BY active DESC, name").fetchall()
    except Exception as e:
        st.error(f"خطأ في جلب الخدمات: {e}")
        return
    
    for service in services:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(service['name'])
        with col2:
            status = "مفعلة" if service['active'] else "معطلة"
            st.write(status)
        with col3:
            if st.button("تغيير الحالة" if service['active'] else "تفعيل", key=f"toggle_{service['id']}"):
                try:
                    with get_conn() as conn:
                        new_status = 0 if service['active'] else 1
                        conn.execute("UPDATE services SET active=? WHERE id=?", (new_status, service['id']))
                        conn.commit()
                    st.success("تم تغيير الحالة")
                    st.cache_data.clear()
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ في تغيير الحالة: {e}")
    
    # إضافة خدمة جديدة
    with st.form("add_service"):
        sname = st.text_input("إضافة خدمة جديدة", max_chars=100)
        s_active = st.checkbox("مفعلة؟", value=True)
        sub = st.form_submit_button("إضافة الخدمة")
        
        if sub and sname:
            try:
                with get_conn() as conn:
                    conn.execute("INSERT INTO services (name, active) VALUES (?,?)", (sname.strip(), 1 if s_active else 0))
                    conn.commit()
                st.success("تمت الإضافة")
                st.cache_data.clear()
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("الخدمة موجودة مسبقًا")
            except Exception as e:
                st.error(f"خطأ في الإضافة: {e}")
    
    # إدارة أنواع المستشفيات
    st.markdown("#### 🏥 أنواع المستشفيات")
    types = get_hospital_types()
    editable = st.text_input("أنواع المستشفيات (مفصولة بفواصل)", ",".join(types))
    if st.button("حفظ الأنواع"):
        new_types = [t.strip() for t in editable.split(",") if t.strip()]
        if new_types:
            set_hospital_types(new_types)
            st.success("تم الحفظ")
            time.sleep(0.5)
            st.rerun()
    
    # إدارة القطاعات
    st.markdown("#### 🏢 القطاعات")
    sectors = get_sectors()
    editable_sectors = st.text_input("القطاعات (مفصولة بفواصل)", ",".join(sectors))
    if st.button("حفظ القطاعات"):
        new_sectors = [s.strip() for s in editable_sectors.split(",") if s.strip()]
        if new_sectors:
            set_sectors(new_sectors)
            st.success("تم الحفظ")
            time.sleep(0.5)
            st.rerun()
    
    # إدارة المحافظات
    st.markdown("#### 🗺️ المحافظات")
    gov = get_governorates()
    editable_gov = st.text_input("المحافظات (مفصولة بفواصل)", ",".join(gov))
    if st.button("حفظ المحافظات"):
        new_gov = [g.strip() for g in editable_gov.split(",") if g.strip()]
        if new_gov:
            set_governorates(new_gov)
            st.success("تم الحفظ")
            time.sleep(0.5)
            st.rerun()
    
    # إدارة حالات الطلبات
    st.markdown("#### 📋 حالات الطلبات (للأدمن فقط)")
    current_statuses = get_request_statuses()
    st.write("الحالات الحالية: " + ", ".join(current_statuses))
    
    # إضافة/تعديل حالة
    with st.form("add_edit_status"):
        new_status_name = st.text_input("اسم الحالة الجديدة أو تعديل الحالية", max_chars=100)
        selected_status_for_edit = st.selectbox("اختر حالة لتعديل إعداداتها", [""] + current_statuses)
        prevents_new = st.checkbox("يمنع تقديم طلب جديد لنفس الخدمة", value=False)
        blocks_days = st.number_input("يمنع تقديم طلب لنفس الخدمة لمدة (أيام) - 0 للتعطيل", min_value=0, value=0)
        is_final = st.checkbox("حالة نهائية (تغلق الطلب)", value=False)
        
        if st.form_submit_button("إضافة/تعديل الحالة"):
            if new_status_name:
                try:
                    with get_conn() as conn:
                        conn.execute("INSERT OR IGNORE INTO request_statuses (name) VALUES (?)", (new_status_name,))
                        conn.execute("""
                            INSERT INTO status_settings (status_name, prevents_new_request, blocks_service_for_days, is_final_state)
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT(status_name) DO UPDATE SET
                            prevents_new_request=excluded.prevents_new_request,
                            blocks_service_for_days=excluded.blocks_service_for_days,
                            is_final_state=excluded.is_final_state
                        """, (new_status_name, 1 if prevents_new else 0, blocks_days, 1 if is_final else 0))
                        conn.commit()
                    st.success(f"تمت إضافة أو تعديل الحالة: {new_status_name}")
                    st.cache_data.clear()
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ: {e}")
            else:
                st.warning("يرجى إدخال اسم الحالة.")
    
    # حذف حالة
    with st.form("delete_status"):
        status_to_delete = st.selectbox("اختر حالة لحذفها", [""] + [s for s in current_statuses if s != "طلب غير مكتمل"])
        if st.form_submit_button("حذف الحالة"):
            if status_to_delete:
                try:
                    with get_conn() as conn:
                        count = conn.execute("SELECT COUNT(*) as c FROM requests WHERE status = ?", (status_to_delete,)).fetchone()['c']
                        if count > 0:
                            st.warning(f"لا يمكن حذف الحالة '{status_to_delete}' لأنها مستخدمة في {count} طلب(طلبات).")
                        else:
                            conn.execute("DELETE FROM status_settings WHERE status_name = ?", (status_to_delete,))
                            conn.execute("DELETE FROM request_statuses WHERE name = ?", (status_to_delete,))
                            conn.commit()
                            st.success(f"تم حذف الحالة: {status_to_delete}")
                            st.cache_data.clear()
                            time.sleep(0.5)
                            st.rerun()
                except Exception as e:
                    st.error(f"خطأ: {e}")
            else:
                st.warning("يرجى اختيار حالة للحذف.")
    
    # إدارة أنواع المستندات
    st.markdown("#### 📄 أنواع المستندات المطلوبة (للأدمن فقط)")
    doc_types = get_document_types()
    
    for doc in doc_types:
        with st.expander(f"تعديل: {doc['display_name']} ({doc['name']})"):
            new_display_name = st.text_input("الاسم المعروض", value=doc['display_name'], key=f"display_{doc['name']}", max_chars=200)
            new_is_video_allowed = st.checkbox("هل يسمح برفع فيديو؟", value=bool(doc['is_video_allowed']), key=f"video_{doc['name']}")
            
            if st.button("حفظ التعديل", key=f"save_doc_{doc['name']}"):
                try:
                    with get_conn() as conn:
                        # تحديث نوع المستند
                        conn.execute("UPDATE document_types SET display_name = ?, is_video_allowed = ? WHERE name = ?", 
                                   (new_display_name, 1 if new_is_video_allowed else 0, doc['name']))
                        
                        # تحديث المستندات الموجودة في الطلبات
                        conn.execute("UPDATE documents SET display_name = ?, is_video_allowed = ? WHERE doc_type = ?", 
                                   (new_display_name, 1 if new_is_video_allowed else 0, doc['name']))
                        
                        conn.commit()
                    st.success("تم حفظ التعديل وتطبيقه على جميع الطلبات")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ في الحفظ: {e}")
    
    # إضافة نوع مستند جديد
    with st.form("add_doc_type"):
        st.markdown("##### إضافة نوع مستند جديد")
        new_doc_name = st.text_input("الاسم الداخلي (لا يمكن تغييره لاحقًا)", max_chars=200)
        new_doc_display_name = st.text_input("الاسم المعروض", max_chars=200)
        new_doc_is_video_allowed = st.checkbox("هل يسمح برفع فيديو؟")
        
        if st.form_submit_button("إضافة نوع مستند"):
            if new_doc_name and new_doc_display_name:
                try:
                    with get_conn() as conn:
                        # إضافة نوع المستند الجديد
                        conn.execute("INSERT INTO document_types (name, display_name, is_video_allowed) VALUES (?, ?, ?)", 
                                   (new_doc_name, new_doc_display_name, 1 if new_doc_is_video_allowed else 0))
                        
                        # إضافة المستند للطلبات الموجودة
                        existing_requests = conn.execute("SELECT DISTINCT r.id, h.type FROM requests r JOIN hospitals h ON r.hospital_id = h.id WHERE r.deleted_at IS NULL").fetchall()
                        for req in existing_requests:
                            hospital_type = req['type']
                            optional_docs = get_optional_docs_for_type(hospital_type)
                            is_required = 0 if new_doc_name in optional_docs else 1
                            conn.execute("INSERT OR IGNORE INTO documents (request_id, doc_type, display_name, required, satisfied, uploaded_at, is_video_allowed) VALUES (?, ?, ?, ?, 0, NULL, ?)", 
                                       (req['id'], new_doc_name, new_doc_display_name, is_required, 1 if new_doc_is_video_allowed else 0))
                        
                        conn.commit()
                    st.success("تمت إضافة نوع المستند وتطبيقه على الطلبات الموجودة")
                    time.sleep(0.5)
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("الاسم الداخلي موجود مسبقًا")
                except Exception as e:
                    st.error(f"خطأ: {e}")
            else:
                st.warning("يرجى ملء الحقول المطلوبة.")
    
    # إدارة المستندات الاختيارية
    st.markdown("#### 📄 إدارة المستندات الاختيارية لأنواع المستشفيات")
    hospital_types = get_hospital_types()
    all_doc_names = [dt['name'] for dt in get_document_types()]
    
    if hospital_types:
        for htype in hospital_types:
            with st.expander(f"تعديل المستندات لـ {htype}", expanded=False):
                st.markdown(f"### {htype}")
                current_optional_docs = get_optional_docs_for_type(htype)
                selected_optional_docs = st.multiselect(
                    f"اختر المستندات الاختيارية لـ {htype}",
                    options=all_doc_names,
                    default=list(current_optional_docs),
                    key=f"multiselect_optional_docs_{htype}"
                )
                
                if st.button(f"💾 حفظ التغييرات لـ {htype}", key=f"save_button_{htype}"):
                    try:
                        set_optional_docs_for_type(htype, selected_optional_docs)
                        
                        # تطبيق التغييرات على الطلبات الموجودة
                        with get_conn() as conn:
                            requests = conn.execute("SELECT r.id FROM requests r JOIN hospitals h ON r.hospital_id = h.id WHERE h.type = ? AND r.deleted_at IS NULL", (htype,)).fetchall()
                            
                            for req in requests:
                                for doc_name in all_doc_names:
                                    is_required = 0 if doc_name in selected_optional_docs else 1
                                    conn.execute("UPDATE documents SET required = ? WHERE request_id = ? AND doc_type = ?", (is_required, req['id'], doc_name))
                            
                            conn.commit()
                        
                        st.success(f"✅ تم حفظ المستندات الاختيارية لـ {htype} وتطبيقها على الطلبات الموجودة")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ حدث خطأ أثناء الحفظ: {e}")

def admin_users_ui() -> None:
    """إدارة المستخدمين"""
    st.markdown("<div class='subheader'>إدارة المستخدمين</div>", unsafe_allow_html=True)
    
    # المستخدمون الإداريون
    st.markdown("#### 👤 المستخدمون الإداريون")
    try:
        with get_conn() as conn:
            admins = conn.execute("SELECT id, username, role FROM admins ORDER BY id").fetchall()
    except Exception as e:
        st.error(f"خطأ في جلب المستخدمين الإداريين: {e}")
        return
    
    for admin in admins:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.markdown(f"<div style='padding: 10px;'><b>{admin['username']}</b> ({admin['role']})</div>", unsafe_allow_html=True)
        with col2:
            if st.button("🗑️ حذف", key=f"del_admin_{admin['id']}") and admin['username'] != 'admin':
                try:
                    with get_conn() as conn:
                        conn.execute("DELETE FROM admins WHERE id=?", (admin['id'],))
                        conn.commit()
                    st.success("تم الحذف")
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ في الحذف: {e}")
        with col3:
            if st.button("إعادة تعيين كلمة المرور", key=f"reset_admin_{admin['id']}"):
                try:
                    with get_conn() as conn:
                        new_password = "1234"
                        conn.execute("UPDATE admins SET password_hash=? WHERE id=?", (secure_hash(new_password), admin['id']))
                        conn.commit()
                    st.success(f"تمت إعادة تعيين كلمة المرور إلى: {new_password}")
                except Exception as e:
                    st.error(f"خطأ في إعادة تعيين كلمة المرور: {e}")
        with col4:
            st.write("")
    
    # إضافة مستخدم إداري
    st.markdown("#### ➕ إضافة مستخدم")
    with st.form("add_admin"):
        u = st.text_input("اسم المستخدم", max_chars=50)
        p = st.text_input("كلمة المرور", type="password", max_chars=100)
        role = st.selectbox("الدور", ["admin", "reviewer"])
        sub = st.form_submit_button("إضافة")
        
        if sub:
            if not u or not p:
                st.error("يرجى ملء جميع الحقول")
            else:
                try:
                    with get_conn() as conn:
                        conn.execute("INSERT INTO admins (username, password_hash, role) VALUES (?,?,?)", (u, secure_hash(p), role))
                        conn.commit()
                    st.success("تمت الإضافة")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("اسم المستخدم موجود مسبقًا")
                except Exception as e:
                    st.error(f"خطأ في الإضافة: {e}")
    
    # إعادة تعيين كلمة المرور
    st.markdown("#### 🔁 إعادة تعيين كلمة المرور")
    with st.form("reset_password"):
        user_type = st.radio("نوع المستخدم", ["مستشفى", "إداري"])
        
        if user_type == "مستشفى":
            try:
                with get_conn() as conn:
                    hospitals = conn.execute("SELECT id, name, username FROM hospitals ORDER BY name").fetchall()
            except Exception as e:
                st.error(f"خطأ في جلب المستشفيات: {e}")
                hospitals = []
            
            if hospitals:
                hospital_options = [f"{h['id']} - {h['name']} ({h['username']})" for h in hospitals]
                selected_hospital = st.selectbox("اختر المستشفى", hospital_options)
                new_password = st.text_input("كلمة المرور الجديدة", type="password", value="1234", max_chars=100)
                
                if st.form_submit_button("إعادة تعيين"):
                    if selected_hospital and new_password:
                        hospital_id = int(selected_hospital.split(" - ")[0])
                        try:
                            with get_conn() as conn:
                                conn.execute("UPDATE hospitals SET password_hash=? WHERE id=?", (secure_hash(new_password), hospital_id))
                                conn.commit()
                            st.success(f"تمت إعادة تعيين كلمة المرور للمستشفى: {selected_hospital}")
                        except Exception as e:
                            st.error(f"خطأ في إعادة تعيين كلمة المرور: {e}")
            else:
                st.info("لا توجد مستشفيات مسجلة")
        
        else:
            try:
                with get_conn() as conn:
                    admins = conn.execute("SELECT id, username FROM admins ORDER BY username").fetchall()
            except Exception as e:
                st.error(f"خطأ في جلب المستخدمين الإداريين: {e}")
                admins = []
            
            if admins:
                admin_options = [f"{a['id']} - {a['username']}" for a in admins]
                selected_admin = st.selectbox("اختر المستخدم الإداري", admin_options)
                new_password = st.text_input("كلمة المرور الجديدة", type="password", max_chars=100)
                
                if st.form_submit_button("إعادة تعيين"):
                    if selected_admin and new_password:
                        admin_id = int(selected_admin.split(" - ")[0])
                        try:
                            with get_conn() as conn:
                                conn.execute("UPDATE admins SET password_hash=? WHERE id=?", (secure_hash(new_password), admin_id))
                                conn.commit()
                            st.success(f"تمت إعادة تعيين كلمة المرور للمستخدم: {selected_admin}")
                        except Exception as e:
                            st.error(f"خطأ في إعادة تعيين كلمة المرور: {e}")
            else:
                st.info("لا يوجد مستخدمين إداريين لإعادة تعيين كلمات مرورهم")

def admin_resources_ui() -> None:
    """إدارة ملفات التنزيل"""
    st.markdown("<div class='subheader'>إدارة ملفات التنزيل</div>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>يمكنك رفع الملفات التالية لجعلها متوفرة للمستخدمين</div>", unsafe_allow_html=True)
    
    RESOURCES_DIR.mkdir(exist_ok=True)
    
    for filename in RESOURCE_FILES:
        filepath = RESOURCES_DIR / filename
        st.markdown(f"#### {filename}")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if filepath.exists():
                st.success("✅ الملف متوفر")
                try:
                    with open(filepath, "rb") as f:
                        st.download_button(
                            label="📥 تنزيل الملف الحالي",
                            data=f,
                            file_name=filename,
                            mime="application/pdf",
                            key=f"download_{filename}"
                        )
                except Exception as e:
                    st.error(f"خطأ في تحميل الملف: {e}")
            else:
                st.warning("⚠️ الملف غير متوفر")
        
        with col2:
            uploaded_file = st.file_uploader("رفع ملف جديد", type=["pdf"], key=f"upload_{filename}")
            if uploaded_file is not None:
                try:
                    # التحقق من حجم الملف
                    if uploaded_file.size > 50 * 1024 * 1024:  # 50MB
                        st.error("حجم الملف كبير جداً (الحد الأقصى 50MB)")
                        continue
                    
                    with open(filepath, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.success("تم رفع الملف بنجاح")
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ في رفع الملف: {e}")

# ---------------------------- الدالة الرئيسية ---------------------------- #
def main() -> None:
    """الدالة الرئيسية للتطبيق"""
    # إعدادات الصفحة الأساسية
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🏨",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # عرض البنر في الأعلى
    banner_path = None
    for ext in ['.png', '.jpg', '.jpeg']:
        path = Path(f"static/banner{ext}")
        if path.exists():
            banner_path = path
            break
    
    if "user" in st.session_state and banner_path:
        try:
            with open(banner_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            st.markdown(
                f"<div style='text-align: center;'><img src='data:image/png;base64,{encoded_string}' class='banner-image'></div>",
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error(f"خطأ في تحميل البنر: {e}")
    
    # تهيئة قاعدة البيانات
    if 'db_setup_done' not in st.session_state:
        try:
            run_ddl()
            run_migrations()
            st.session_state.db_setup_done = True
        except Exception as e:
            st.error(f"❌ خطأ في تهيئة النظام: {e}")
            st.error("يرجى إعادة تحميل الصفحة أو التواصل مع الدعم الفني")
            return
    
    # التحقق من حالة تسجيل الدخول
    if "user" not in st.session_state:
        login_ui()
    else:
        role = st.session_state.user.get("role")
        
        # رسالة ترحيبية
        if "welcome_shown" not in st.session_state:
            user_name = st.session_state.user.get("name", st.session_state.user.get("username", "المستخدم"))
            st.toast(f"مرحباً بعودتك {user_name}! 👋", icon="🏨")
            st.session_state.welcome_shown = True
        
        # توجيه المستخدم بناءً على الدور
        try:
            if role == "hospital":
                hospital_home()
            elif role in ["admin", "reviewer"]:
                admin_home()
            else:
                st.error("❌ دور المستخدم غير معروف")
                st.session_state.pop("user", None)
                st.rerun()
        except Exception as e:
            st.error(f"❌ حدث خطأ في النظام: {e}")
            st.error("يرجى إعادة تحميل الصفحة")
    
    # تذييل الصفحة
    st.markdown("""
        <div class='footer'>
            <div style="text-align: center; padding: 20px;">
                <p style="margin: 0; font-weight: 600; color: #1e40af; font-size: 16px;">
                    © 2025 المشروع القومي لقوائم الانتظار
                </p>
                <p style="margin: 8px 0 0 0; color: #64748b; font-size: 14px;">
                    تصميم وتطوير: الغرفة المركزية لقوائم الانتظار
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("""
        **❌ حدث خطأ غير متوقع في النظام**
        
        يرجى:
        1. تحديث الصفحة
        2. التأكد من اتصال الإنترنت
        3. التواصل مع الدعم الفني إذا استمرت المشكلة
        """)
        # لإظهار الخطأ الفعلي في الطرفية أثناء التطوير
        import traceback
        traceback.print_exc()