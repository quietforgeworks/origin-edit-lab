// Authored passive observer: no Origin parsing and no value/curve mutation.
#include <QSignalSpy>
#include <QPointF>
#include <QVector>
#include <QSet>
#include <QJsonArray>
#include <QJsonObject>
#include <QJsonDocument>
struct Watched {QObject* object;QSignalSpy* spy;};
static QVector<Watched> watched;
static QSet<QObject*> seen;
static QString bits(double value){uint64_t b;memcpy(&b,&value,8);return QString("%1").arg(b,16,16,QChar('0'));}
static void findCurves(QAbstractItemModel*m,QModelIndex p={},int depth=0){
 if(depth>9)return;
 for(int r=0;r<m->rowCount(p);r++){
  auto idx=m->index(r,0,p);
  if(m->data(m->index(r,1,p)).toString()=="Plot"){
   auto*o=static_cast<QObject*>(idx.internalPointer());
   if(o&&QString(o->metaObject()->className())=="XYCurve"&&!seen.contains(o)){
    seen.insert(o);QSignalSpy*spy=nullptr;
    for(int k=0;k<o->metaObject()->methodCount();k++){
     auto mm=o->metaObject()->method(k);
     if(mm.methodType()==QMetaMethod::Signal&&mm.name()=="pointsUpdated"){spy=new QSignalSpy(o,mm);break;}
    }
    watched.append({o,spy});
   }
  }
  auto c=m->index(0,0,idx);if(c.isValid()&&c.parent()==idx)findCurves(m,idx,depth+1);
 }
}
static void watchCurve(){
 for(auto*w:QApplication::allWidgets())if(w->isVisible())if(auto*v=qobject_cast<QTreeView*>(w))if(v->model())findCurves(v->model());
 fprintf(stderr,"Observed %lld actual XYCurve objects\n",(long long)watched.size());
}
static void recordCurve(){
 QJsonObject out;out["method"]="Actual imported XYCurve pointers; public bound-column paths and binary64 APIs; passive pointsUpdated signal";out["curve_count"]=watched.size();
 void*lib=dlopen(qEnvironmentVariable("OBSERVER_BUNDLED_LIB").toUtf8().constData(),RTLD_LAZY|RTLD_LOCAL);
 auto xcol=(const void*(*)(const void*))dlsym(lib,"_ZNK7XYCurve7xColumnEv");
 auto ycol=(const void*(*)(const void*))dlsym(lib,"_ZNK7XYCurve7yColumnEv");
 auto rowCount=(int(*)(const void*))dlsym(lib,"_ZNK6Column8rowCountEv");
 auto valueAt=(double(*)(const void*,int))dlsym(lib,"_ZNK6Column7valueAtEi");
 auto valid=(bool(*)(const void*,int))dlsym(lib,"_ZNK14AbstractColumn7isValidEi");
 auto masked=(bool(*)(const void*,int))dlsym(lib,"_ZNK14AbstractColumn8isMaskedEi");
 auto path=(QString(*)(const void*))dlsym(lib,"_ZNK14AbstractAspect4pathEv");
 QJsonArray curves;
 if(xcol&&ycol&&rowCount&&valueAt&&valid&&masked&&path)for(auto w:watched){
  QJsonObject c;c["curve_path"]=path(w.object);c["signal_spy_valid"]=w.spy&&w.spy->isValid();
  auto*x=xcol(w.object);auto*y=ycol(w.object);c["x_bound"]=x!=nullptr;c["y_bound"]=y!=nullptr;
  if(x&&y){
   c["x_path"]=path(x);c["y_path"]=path(y);c["x_allocated_rows"]=rowCount(x);c["y_allocated_rows"]=rowCount(y);
   // Separate arrays: never zip unequal columns or silently truncate.
   for(auto pair:{qMakePair(QString("x"),x),qMakePair(QString("y"),y)}){
    QJsonArray values;
    for(int r=0;r<rowCount(pair.second);r++){QJsonObject cell;cell["row"]=r;cell["bits"]=bits(valueAt(pair.second,r));cell["valid"]=valid(pair.second,r);cell["masked"]=masked(pair.second,r);values.append(cell);}
    c[pair.first+"_values"]=values;
   }
  }
  QJsonArray emissions;
  if(w.spy)for(const auto&args:*w.spy){QJsonObject e;e["start_index"]=args.at(1).toInt();e["end_index"]=args.at(2).toInt();auto points=args.at(3).value<QList<QPointF>>();e["logical_point_count"]=points.size();QJsonArray pp;for(const auto&p:points){QJsonArray a;a.append(bits(p.x()));a.append(bits(p.y()));pp.append(a);}e["logical_points_binary64"]=pp;emissions.append(e);}
  c["point_signal_emissions"]=emissions;curves.append(c);
 }
 out["curves"]=curves;QFile f(qEnvironmentVariable("OBSERVER_OUT")+"/curve-observation.json");f.open(QIODevice::WriteOnly);f.write(QJsonDocument(out).toJson());
}
